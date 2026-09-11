import os
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.schemas.document import ReuploadRequestCreate, DocumentResponse
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.document import Document, DocumentType
from app.db.models.vehicle import Vehicle
from app.core.dependencies import get_current_master, get_current_admin, get_current_master_or_admin
from app.services import document_service, vehicle_service
from app.utils.file_validation import validate_and_save_upload_file
from app.core.config import settings
from app.core.security import decode_token
from app.core.exceptions import PermissionDeniedException, NotFoundException, CredentialsException

router = APIRouter(prefix="/documents", tags=["Vehicle Documents"])

def populate_doc_response(db: Session, doc: Document) -> DocumentResponse:
    res = DocumentResponse.model_validate(doc)
    if doc.vehicle:
        res.vehicle_number = doc.vehicle.vehicle_number
    else:
        v = db.query(Vehicle).filter(Vehicle.id == doc.vehicle_id).first()
        if v:
            res.vehicle_number = v.vehicle_number
    return res

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    vehicle_id: int = Form(...),
    document_type: DocumentType = Form(...),
    expiry_date: date = Form(...),
    document_number: Optional[str] = Form(None),
    issue_date: Optional[date] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    master: User = Depends(get_current_master)
):
    """Master endpoint to upload initial vehicle documents or re-upload if approved by Admin."""
    vehicle_service.get_vehicle_by_id(db, vehicle_id)
    filename, file_url, mime_type, file_size = validate_and_save_upload_file(file, vehicle_id)
    
    doc = document_service.create_document(
        db=db,
        vehicle_id=vehicle_id,
        document_type=document_type,
        document_number=document_number,
        issue_date=issue_date,
        expiry_date=expiry_date,
        file_name=filename,
        file_url=file_url,
        mime_type=mime_type,
        file_size=file_size,
        user_id=master.id,
        is_driver=False
    )
    return populate_doc_response(db, doc)


@router.post("/{document_id}/request-reupload", response_model=DocumentResponse)
def request_reupload(
    document_id: int,
    payload: Optional[ReuploadRequestCreate] = None,
    db: Session = Depends(get_db),
    master: User = Depends(get_current_master)
):
    """Master endpoint to request reupload permission from Admin with a reason."""
    reason = payload.reason if payload else None
    doc = document_service.request_reupload_permission(db, document_id, master.id, reason)
    return populate_doc_response(db, doc)


@router.post("/{document_id}/allow-reupload", response_model=DocumentResponse)
def allow_reupload(
    document_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Admin endpoint to approve Master's document re-upload request."""
    doc = document_service.grant_reupload_permission(db, document_id, admin.id)
    return populate_doc_response(db, doc)


@router.post("/{document_id}/reject-reupload", response_model=DocumentResponse)
def reject_reupload(
    document_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Admin endpoint to reject Master's document re-upload request."""
    doc = document_service.reject_reupload_permission(db, document_id, admin.id)
    return populate_doc_response(db, doc)


@router.get("/reupload-requests", response_model=List[DocumentResponse])
def get_reupload_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_master_or_admin)
):
    """List all documents with pending reupload requests awaiting Admin approval."""
    docs = document_service.get_pending_reupload_requests(db)
    return [populate_doc_response(db, d) for d in docs]


@router.get("/vehicle/{vehicle_id}", response_model=List[DocumentResponse])
def get_documents_by_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_master_or_admin)
):
    """Get all documents for a vehicle (accessible to Master and Admin monitors)."""
    vehicle_service.get_vehicle_by_id(db, vehicle_id)
    docs = document_service.get_documents_for_vehicle(db, vehicle_id)
    return [populate_doc_response(db, d) for d in docs]


@router.get("/expired", response_model=List[DocumentResponse])
def get_expired_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_master_or_admin)
):
    """Get all expired documents across fleet (Master and Admin monitors)."""
    docs = document_service.get_expired_documents(db)
    return [populate_doc_response(db, d) for d in docs]


@router.get("/expiring-soon", response_model=List[DocumentResponse])
def get_expiring_soon_documents(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_master_or_admin)
):
    """Get documents expiring within specified days (Master and Admin monitors)."""
    docs = document_service.get_expiring_soon_documents(db, days)
    return [populate_doc_response(db, d) for d in docs]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    master: User = Depends(get_current_master)
):
    """Master endpoint to delete a document."""
    document_service.delete_document(db, document_id, master.id)


@router.get("/file/{filename}")
def serve_document_file(
    filename: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Serve secure document file for authenticated users."""
    if not token:
        raise CredentialsException("Authentication token required to view document")
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise CredentialsException("User account invalid or inactive")
    except Exception:
        raise CredentialsException("Invalid or expired token")

    safe_filename = os.path.basename(filename)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    if not os.path.exists(file_path):
        raise NotFoundException("Requested file not found")

    doc = db.query(Document).filter(Document.file_name == safe_filename).first()
    media_type = doc.mime_type if doc else None

    return FileResponse(
        file_path,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename=\"{safe_filename}\""}
    )
