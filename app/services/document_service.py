from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.document import Document, DocumentType, DocumentStatus
from app.db.models.audit_log import AuditLog
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.core.exceptions import NotFoundException, BadRequestException, PermissionDeniedException

def compute_document_status(expiry_date: date) -> DocumentStatus:
    today = date.today()
    if expiry_date < today:
        return DocumentStatus.EXPIRED
    elif expiry_date <= today + timedelta(days=30):
        return DocumentStatus.EXPIRING_SOON
    return DocumentStatus.VALID

def create_or_update_document(
    db: Session,
    vehicle_id: int,
    document_type: DocumentType,
    document_number: Optional[str],
    issue_date: Optional[date],
    expiry_date: date,
    file_name: str,
    file_url: str,
    mime_type: str,
    file_size: int,
    user_id: int,
    is_driver: bool = False
) -> Document:
    existing_doc = db.query(Document).filter(
        Document.vehicle_id == vehicle_id,
        Document.document_type == document_type
    ).first()

    status = compute_document_status(expiry_date)

    if existing_doc:
        if is_driver and not existing_doc.can_reupload:
            raise PermissionDeniedException(
                "Document has already been uploaded for this vehicle. You need permission from an admin to update or re-upload it."
            )
        
        existing_doc.document_number = document_number
        existing_doc.issue_date = issue_date
        existing_doc.expiry_date = expiry_date
        existing_doc.file_name = file_name
        existing_doc.file_url = file_url
        existing_doc.mime_type = mime_type
        existing_doc.file_size = file_size
        existing_doc.uploaded_by = user_id
        existing_doc.status = status
        existing_doc.can_reupload = False  # Reset permission after update
        existing_doc.reupload_requested = False
        existing_doc.reupload_reason = None
        
        db.commit()
        db.refresh(existing_doc)
        
        audit = AuditLog(user_id=user_id, action="UPDATE_DOCUMENT", entity_type="document", entity_id=existing_doc.id)
        db.add(audit)
        db.commit()
        return existing_doc
    else:
        doc = Document(
            vehicle_id=vehicle_id,
            document_type=document_type,
            document_number=document_number,
            issue_date=issue_date,
            expiry_date=expiry_date,
            file_name=file_name,
            file_url=file_url,
            mime_type=mime_type,
            file_size=file_size,
            uploaded_by=user_id,
            status=status,
            can_reupload=False
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        audit = AuditLog(user_id=user_id, action="UPLOAD_DOCUMENT", entity_type="document", entity_id=doc.id)
        db.add(audit)
        db.commit()
        return doc

def create_document(
    db: Session,
    vehicle_id: int,
    document_type: DocumentType,
    document_number: Optional[str],
    issue_date: Optional[date],
    expiry_date: date,
    file_name: str,
    file_url: str,
    mime_type: str,
    file_size: int,
    user_id: int,
    is_driver: bool = False
) -> Document:
    return create_or_update_document(
        db=db,
        vehicle_id=vehicle_id,
        document_type=document_type,
        document_number=document_number,
        issue_date=issue_date,
        expiry_date=expiry_date,
        file_name=file_name,
        file_url=file_url,
        mime_type=mime_type,
        file_size=file_size,
        user_id=user_id,
        is_driver=is_driver
    )

def grant_reupload_permission(db: Session, document_id: int, admin_id: int) -> Document:
    doc = get_document_by_id(db, document_id)
    doc.can_reupload = True
    doc.reupload_requested = False
    doc.reupload_reason = None
    db.commit()
    db.refresh(doc)
    
    audit = AuditLog(
        user_id=admin_id,
        action="GRANT_DOCUMENT_REUPLOAD",
        entity_type="document",
        entity_id=doc.id
    )
    db.add(audit)
    db.commit()
    return doc

def get_documents_for_vehicle(db: Session, vehicle_id: int) -> List[Document]:
    docs = db.query(Document).filter(Document.vehicle_id == vehicle_id).all()
    updated = False
    for doc in docs:
        if doc.can_reupload is None:
            doc.can_reupload = False
            updated = True
        if doc.reupload_requested is None:
            doc.reupload_requested = False
            updated = True
        new_status = compute_document_status(doc.expiry_date)
        if doc.status != new_status:
            doc.status = new_status
            updated = True
    if updated:
        db.commit()
    return docs

def get_document_by_id(db: Session, document_id: int) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise NotFoundException("Document not found")
    new_status = compute_document_status(doc.expiry_date)
    if doc.status != new_status:
        doc.status = new_status
        db.commit()
    return doc

def get_expired_documents(db: Session) -> List[Document]:
    today = date.today()
    docs = db.query(Document).filter(Document.expiry_date < today).all()
    for doc in docs:
        if doc.status != DocumentStatus.EXPIRED:
            doc.status = DocumentStatus.EXPIRED
    db.commit()
    return docs

def get_expiring_soon_documents(db: Session, days: int = 30) -> List[Document]:
    today = date.today()
    future_date = today + timedelta(days=days)
    docs = db.query(Document).filter(
        Document.expiry_date >= today,
        Document.expiry_date <= future_date
    ).all()
    for doc in docs:
        if doc.status != DocumentStatus.EXPIRING_SOON:
            doc.status = DocumentStatus.EXPIRING_SOON
    db.commit()
    return docs

def delete_document(db: Session, document_id: int, user_id: int, is_driver: bool = False) -> None:
    doc = get_document_by_id(db, document_id)
    if is_driver and not doc.can_reupload:
        raise PermissionDeniedException("Permission from admin is required to modify or delete this document.")
        
    db.delete(doc)
    db.commit()
    
    audit = AuditLog(user_id=user_id, action="DELETE_DOCUMENT", entity_type="document", entity_id=document_id)
    db.add(audit)
    db.commit()



def request_reupload_permission(
    db: Session, 
    document_id: int, 
    user_id: int, 
    reason: Optional[str] = None
) -> Document:
    doc = get_document_by_id(db, document_id)
    doc.reupload_requested = True
    doc.reupload_reason = reason
    db.commit()
    db.refresh(doc)
    
    audit = AuditLog(
        user_id=user_id,
        action="REQUEST_DOCUMENT_REUPLOAD",
        entity_type="document",
        entity_id=doc.id,
        details=f"Reason: {reason}" if reason else None
    )
    db.add(audit)
    db.commit()
    return doc


def get_pending_reupload_requests(db:Session) -> List[Document]:
    return db.query(Document).filter(Document.reupload_requested == True).all()