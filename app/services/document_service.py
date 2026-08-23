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
    user_id: int
) -> Document:
    status = compute_document_status(expiry_date)
    
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
        status=status
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    audit = AuditLog(user_id=user_id, action="UPLOAD_DOCUMENT", entity_type="document", entity_id=doc.id)
    db.add(audit)
    db.commit()
    return doc

def get_documents_for_vehicle(db: Session, vehicle_id: int) -> List[Document]:
    # Update statuses dynamically before returning
    docs = db.query(Document).filter(Document.vehicle_id == vehicle_id).all()
    for doc in docs:
        new_status = compute_document_status(doc.expiry_date)
        if doc.status != new_status:
            doc.status = new_status
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

def delete_document(db: Session, document_id: int, user_id: int) -> None:
    doc = get_document_by_id(db, document_id)
    db.delete(doc)
    db.commit()
    
    audit = AuditLog(user_id=user_id, action="DELETE_DOCUMENT", entity_type="document", entity_id=document_id)
    db.add(audit)
    db.commit()
