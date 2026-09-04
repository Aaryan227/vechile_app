from app.db.models.user import User, UserRole
from app.db.models.vehicle import Vehicle
from app.db.models.vehicle_assignment import VehicleAssignment
from app.db.models.document import Document, DocumentType, DocumentStatus
from app.db.models.tanker_report import TankerDailyReport
from app.db.models.audit_log import AuditLog
from app.db.models.tax import (
    VehicleTaxRecord,
    VehicleGovernmentCharge,
    VehicleChallan,
    VehicleFASTag,
    TaxType,
    ChargeType,
    TaxStatus,
    ChallanStatus,
    FASTagStatus,
)

__all__ = [
    "User",
    "UserRole",
    "Vehicle",
    "VehicleAssignment",
    "Document",
    "DocumentType",
    "DocumentStatus",
    "TankerDailyReport",
    "AuditLog",
    "VehicleTaxRecord",
    "VehicleGovernmentCharge",
    "VehicleChallan",
    "VehicleFASTag",
    "TaxType",
    "ChargeType",
    "TaxStatus",
    "ChallanStatus",
    "FASTagStatus",
]
