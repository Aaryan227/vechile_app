import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base

class DocumentType(str, enum.Enum):
    RC = "RC"
    INSURANCE = "INSURANCE"
    NATIONAL_PERMIT ="NATIONAL_PERMIT"
    STATE_PERMIT = "STATE_PERMIT"
    FITNESS = "FITNESS"
    PUC = "PUC"
    OTHER = "OTHER"

class DocumentStatus(str, enum.Enum):
    VALID = "VALID"
    EXPIRING_SOON = "EXPIRING_SOON"
    EXPIRED = "EXPIRED"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(Enum(DocumentType), nullable=False)
    document_number = Column(String(100), nullable=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.VALID, nullable=False, index=True)
    can_reupload = Column(Boolean, default=False, nullable=False)
    reupload_requested = Column(Boolean , default=False , index = True)
    reupload_reason = Column(String(500) , nullable = True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    vehicle = relationship("Vehicle", back_populates="documents")
