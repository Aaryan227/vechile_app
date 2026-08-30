from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.db.models.document import DocumentType, DocumentStatus

class DocumentBase(BaseModel):
    document_type: DocumentType
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: date

class DocumentCreate(DocumentBase):
    vehicle_id: int

class DocumentUpdate(BaseModel):
    document_type: Optional[DocumentType] = None
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None

class DocumentResponse(DocumentBase):
    id: int
    vehicle_id: int
    file_name: str
    file_url: str
    mime_type: str
    file_size: int
    uploaded_by: Optional[int] = None
    status: DocumentStatus
    can_reupload: bool = False
    reupload_requested: bool = False
    reupload_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReuploadRequestCreate(BaseModel):
    reason: Optional[str] = None
