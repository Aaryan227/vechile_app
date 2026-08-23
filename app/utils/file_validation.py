import os
import uuid
from typing import Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import BadRequestException

def validate_and_save_upload_file(file: UploadFile, vehicle_id: int) -> Tuple[str, str, str, int]:
    if not file.filename:
        raise BadRequestException("Uploaded file must have a filename")
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise BadRequestException(f"Invalid file extension '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}")
        
    mime_type = file.content_type
    if mime_type not in settings.ALLOWED_MIME_TYPES:
        raise BadRequestException(f"Invalid MIME type '{mime_type}'. Allowed: {', '.join(settings.ALLOWED_MIME_TYPES)}")
        
    # Read file content to check size and save
    contents = file.file.read()
    file_size = len(contents)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise BadRequestException(f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB")
        
    unique_filename = f"vehicle_{vehicle_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(contents)
        
    file_url = f"{settings.API_V1_STR}/documents/file/{unique_filename}"
    return unique_filename, file_url, mime_type, file_size
