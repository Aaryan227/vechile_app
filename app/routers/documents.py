import os
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.document import DocumentType
from app.core.dependencies import get_current_user, get_current_admin
from app.schemas.document import DocumentResponse
from app.services import document_service, vehicle_service
from app.utils.file_validation import validate_and_save_upload_file
from app.core.config import settings
from app.core.exceptions import PermissionDeniedException, NotFoundException

router = APIRouter(prefix="/documents", tags=["Vehicle Documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    vehicle_id: int = Form(...),
    document_type: DocumentType = Form(...),
    expiry_date: date = Form(...),
    document_number: Optional[str] = Form(None),
    issue_date: Optional[date] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Authorization check: verify vehicle exists and driver is assigned to it if driver
    vehicle = vehicle_service.get_vehicle_by_id(db, vehicle_id)
    is_driver = (current_user.role == UserRole.DRIVER)
    if is_driver:
        assigned = vehicle_service.get_driver_assigned_vehicles(db, current_user.id)
        if vehicle.id not in [v.id for v in assigned]:
            raise PermissionDeniedException("You are not assigned to this vehicle")
            
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
        user_id=current_user.id,
        is_driver=is_driver
    )
    return doc

@router.post("/{document_id}/allow-reupload", response_model=DocumentResponse)
def allow_reupload(
    document_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """Admin endpoint to grant permission to driver to re-upload or update a document."""
    return document_service.grant_reupload_permission(db, document_id, admin.id)

@router.get("/vehicle/{vehicle_id}", response_model=List[DocumentResponse])
def get_documents_by_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vehicle = vehicle_service.get_vehicle_by_id(db, vehicle_id)
    if current_user.role == UserRole.DRIVER:
        assigned = vehicle_service.get_driver_assigned_vehicles(db, current_user.id)
        if vehicle.id not in [v.id for v in assigned]:
            raise PermissionDeniedException("Access denied: You are not assigned to this vehicle")
            
    return document_service.get_documents_for_vehicle(db, vehicle_id)

@router.get("/expired", response_model=List[DocumentResponse])
def get_expired_documents(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return document_service.get_expired_documents(db)

@router.get("/expiring-soon", response_model=List[DocumentResponse])
def get_expiring_soon_documents(
    days: int = 30,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    return document_service.get_expiring_soon_documents(db, days)

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    is_driver = (current_user.role == UserRole.DRIVER)
    doc = document_service.get_document_by_id(db, document_id)
    if is_driver and doc.uploaded_by != current_user.id:
        raise PermissionDeniedException("Insufficient permission to delete this document")
        
    document_service.delete_document(db, document_id, current_user.id, is_driver=is_driver)

@router.get("/file/{filename}")
def serve_document_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    if not os.path.exists(file_path):
        raise NotFoundException("Requested file not found")
    return FileResponse(file_path)
