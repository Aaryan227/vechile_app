import os
import logging
from datetime import datetime, timezone , date , timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings
from app.db.models.user import User, UserRole
from app.db.models.device_token import AdminDeviceToken
from app.schemas.notification import DeviceTokenCreate
from app.db.models.document import Document
from app.db.models.vehicle import Vehicle
from app.db.models.notification import UserNotification
from app.core.exceptions import NotFoundException


logger = logging.getLogger(__name__)

_firebase_initialized = False


def get_firebase_credentials_path() -> Optional[str]:
    """Resolve the path to the Firebase service account credentials JSON file."""
    candidate_paths = [
        "/etc/secrets/firebase-key.json",
        settings.FIREBASE_CREDENTIALS_PATH,
        os.path.join(os.getcwd(), settings.FIREBASE_CREDENTIALS_PATH),
        os.path.join(os.getcwd(), "firebase-key.json"),
    ]
    for p in candidate_paths:
        if p and os.path.exists(p):
            return p
    return None


def init_firebase() -> bool:
    """Initialize Firebase Admin SDK if credentials exist and not already initialized."""
    global _firebase_initialized
    if _firebase_initialized or bool(firebase_admin._apps):
        _firebase_initialized = True
        return True

    cred_path = get_firebase_credentials_path()
    if not cred_path:
        logger.warning("Firebase service account credentials not found. Push notifications will be disabled.")
        return False

    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info(f"Firebase Admin SDK initialized successfully using credentials at: {cred_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}", exc_info=True)
        return False


def register_device_token(db: Session, user_id: int, data: DeviceTokenCreate) -> AdminDeviceToken:
    """Register or update an FCM device token for a user."""
    existing = db.query(AdminDeviceToken).filter(
        AdminDeviceToken.device_token == data.device_token
    ).first()

    if existing:
        existing.user_id = user_id
        existing.platform = data.platform or existing.platform
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    record = AdminDeviceToken(
        user_id=user_id,
        device_token=data.device_token,
        platform=data.platform or "android",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def unregister_device_token(db: Session, user_id: int, device_token: str) -> bool:
    """Remove a device token when an Admin logs out from their phone."""
    record = db.query(AdminDeviceToken).filter(
        AdminDeviceToken.user_id == user_id,
        AdminDeviceToken.device_token == device_token
    ).first()

    if record:
        db.delete(record)
        db.commit()
        return True
    return False


def send_push_notification_to_admins(
    db: Session,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
) -> int:
    """
    Send a push notification to all registered Admin mobile devices
    and persist an in-app notification record for the Bell Icon inbox.
    Returns the count of successfully delivered push notifications.
    """
    # 1. Persist notification to database for all active Admins (Bell Icon Inbox)
    try:
        active_admins = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True
        ).all()
        for admin in active_admins:
            notif = UserNotification(
                user_id=admin.id,
                title=title,
                body=body,
                notification_type=str((data or {}).get("type", "")) if data else None,
                data_payload=data or {},
                is_read=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(notif)
        db.commit()
    except Exception as db_err:
        logger.error(f"Failed to record in-app notification in DB: {db_err}", exc_info=True)
        db.rollback()

    # 2. Dispatch FCM Push Notification to registered devices
    if not init_firebase():
        logger.info("Firebase not configured; skipping push notification.")
        return 0

    # Retrieve all device tokens registered to active Admins
    admin_tokens = db.query(AdminDeviceToken).join(
        User, AdminDeviceToken.user_id == User.id
    ).filter(
        User.role == UserRole.ADMIN,
        User.is_active == True
    ).all()

    if not admin_tokens:
        logger.debug("No registered Admin device tokens found for push notification.")
        return 0

    token_strings = [t.device_token for t in admin_tokens]

    # FCM payload data values must all be strings
    safe_data = {str(k): str(v) for k, v in (data or {}).items()}

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=safe_data,
        tokens=token_strings,
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id=settings.FCM_ANDROID_CHANNEL_ID,
                priority="high",
                default_sound=True,
                default_vibrate_timings=True,
            ),
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound="default",
                    badge=1,
                )
            )
        ),
    )

    try:
        response = messaging.send_each_for_multicast(message)
        logger.info(f"Push notifications sent: {response.success_count}/{len(token_strings)} successful.")

        # Prune dead / unregistered tokens
        tokens_to_delete = []
        for idx, resp in enumerate(response.responses):
            if not resp.success:
                err = resp.exception
                # Check for unregistered or invalid token errors
                if hasattr(err, "code") and err.code in ("UNREGISTERED", "INVALID_ARGUMENT", "REGISTRATION_TOKEN_NOT_REGISTERED"):
                    tokens_to_delete.append(token_strings[idx])
                elif "registration-token-not-registered" in str(err).lower() or "unregistered" in str(err).lower():
                    tokens_to_delete.append(token_strings[idx])

        if tokens_to_delete:
            db.query(AdminDeviceToken).filter(
                AdminDeviceToken.device_token.in_(tokens_to_delete)
            ).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Pruned {len(tokens_to_delete)} expired/unregistered FCM tokens.")

        return response.success_count
    except Exception as e:
        logger.error(f"Error sending multicast push notification: {e}", exc_info=True)
        return 0


def check_and_notify_expiring_documents(db: Session, days: int = 7) -> int:
    """Check for documents expiring within the next N days and notify Admins."""
    today = date.today()
    target_date = today + timedelta(days=days)

    expiring_docs = db.query(Document).filter(
        Document.expiry_date >= today,
        Document.expiry_date <= target_date
    ).all()

    if not expiring_docs:
        return 0

    count = 0
    for doc in expiring_docs:
        veh_num = doc.vehicle.vehicle_number if doc.vehicle else f"#{doc.vehicle_id}"
        doc_type_name = doc.document_type.value if hasattr(doc.document_type, "value") else str(doc.document_type)
        days_left = (doc.expiry_date - today).days

        send_push_notification_to_admins(
            db=db,
            title="⏳ Document Expiring Soon",
            body=f"{doc_type_name} for vehicle {veh_num} expires in {days_left} day(s) on {doc.expiry_date}!",
            data={
                "type": "document_expiring_soon",
                "document_id": str(doc.id),
                "vehicle_id": str(doc.vehicle_id),
                "expiry_date": str(doc.expiry_date)
            }
        )
        count += 1

    return count


def check_and_notify_overdue_taxes(db: Session) -> int:
    """Check for tax records whose due date has passed without payment and notify Admins."""
    from app.services import tax_service
    from app.db.models.tax import TaxStatus

    overdue_taxes = tax_service.get_taxes_by_status(db, TaxStatus.OVERDUE)
    if not overdue_taxes:
        return 0

    count = 0
    for tax in overdue_taxes:
        veh_num = tax.vehicle.vehicle_number if tax.vehicle else f"#{tax.vehicle_id}"
        tax_name = tax.tax_type.value.replace("_", " ").title() if hasattr(tax.tax_type, "value") else str(tax.tax_type)
        amt_fmt = f"₹{tax.amount:,.2f}"

        send_push_notification_to_admins(
            db=db,
            title="⚠️ Tax Payment Overdue",
            body=f"{tax_name} ({amt_fmt}) for vehicle {veh_num} is OVERDUE (Due: {tax.due_date})!",
            data={
                "type": "tax_overdue",
                "tax_id": str(tax.id),
                "vehicle_id": str(tax.vehicle_id),
                "amount": str(tax.amount)
            }
        )
        count += 1

    return count


def run_compliance_notification_scan(db: Session, doc_days: int = 7) -> Dict[str, int]:
    """Scans and dispatches notifications for both expiring documents and overdue taxes."""
    docs_notified = check_and_notify_expiring_documents(db=db, days=doc_days)
    taxes_notified = check_and_notify_overdue_taxes(db=db)
    return {
        "expiring_documents_notified": docs_notified,
        "overdue_taxes_notified": taxes_notified,
        "total_notifications_sent": docs_notified + taxes_notified
    }


# ==========================================
# In-App Notification Center (Bell Icon)
# ==========================================

def get_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50
):
    """Retrieve in-app notifications for a user with unread and total counts."""
    query = db.query(UserNotification).filter(UserNotification.user_id == user_id)

    total_count = query.count()
    unread_count = db.query(UserNotification).filter(
        UserNotification.user_id == user_id,
        UserNotification.is_read == False
    ).count()

    if unread_only:
        query = query.filter(UserNotification.is_read == False)

    notifications = query.order_by(UserNotification.created_at.desc()).offset(skip).limit(limit).all()
    return notifications, unread_count, total_count


def get_unread_notification_count(db: Session, user_id: int) -> int:
    """Get the number of unread in-app notifications for a user."""
    return db.query(UserNotification).filter(
        UserNotification.user_id == user_id,
        UserNotification.is_read == False
    ).count()


def mark_notification_as_read(db: Session, notification_id: int, user_id: int) -> UserNotification:
    """Mark a single notification as read."""
    notif = db.query(UserNotification).filter(
        UserNotification.id == notification_id,
        UserNotification.user_id == user_id
    ).first()

    if not notif:
        raise NotFoundException("Notification not found")

    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notif)

    return notif


def mark_all_notifications_as_read(db: Session, user_id: int) -> int:
    """Mark all unread notifications as read for a user."""
    now = datetime.now(timezone.utc)
    updated_count = db.query(UserNotification).filter(
        UserNotification.user_id == user_id,
        UserNotification.is_read == False
    ).update({
        UserNotification.is_read: True,
        UserNotification.read_at: now
    }, synchronize_session=False)

    db.commit()
    return updated_count


def delete_user_notification(db: Session, notification_id: int, user_id: int) -> None:
    """Delete a notification from user's inbox."""
    notif = db.query(UserNotification).filter(
        UserNotification.id == notification_id,
        UserNotification.user_id == user_id
    ).first()

    if not notif:
        raise NotFoundException("Notification not found")

    db.delete(notif)
    db.commit()


