"""File upload utilities for tutor documents."""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from src.config import config


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    
    # Default allowed extensions (always supported)
    default_exts = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'ppt', 'pptx', 'gif', 'txt'}
    
    # Check against default first (this ensures backwards compatibility)
    if ext in default_exts:
        return True
    
    # Also check config.ALLOWED_EXTENSIONS if it exists
    if hasattr(config, 'ALLOWED_EXTENSIONS') and config.ALLOWED_EXTENSIONS:
        # Ensure all extensions in config are lowercase
        allowed_exts = {ext.lower() for ext in config.ALLOWED_EXTENSIONS} if isinstance(config.ALLOWED_EXTENSIONS, (list, tuple, set)) else config.ALLOWED_EXTENSIONS
        return ext in allowed_exts
    
    # Fallback: only allow default extensions
    return ext in default_exts


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    if '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def generate_unique_filename(original_filename: str, tutor_id: int) -> str:
    """Generate a unique filename for uploaded file."""
    ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())[:8]
    secure_name = secure_filename(original_filename.rsplit('.', 1)[0])
    return f"tutor_{tutor_id}_{secure_name}_{unique_id}.{ext}"


def get_upload_path(tutor_id: int, filename: str) -> tuple:
    """
    Get the full upload path and relative path for a file.
    Returns: (full_path, relative_path)
    """
    # Create tutor-specific directory structure: uploads/tutors/{tutor_id}/
    upload_base = config.UPLOAD_DIR
    tutor_dir = os.path.join(upload_base, "tutors", str(tutor_id))
    
    # Ensure directory exists
    os.makedirs(tutor_dir, exist_ok=True)
    
    # Full path for saving
    full_path = os.path.join(tutor_dir, filename)
    
    # Relative path for database storage (relative to uploads directory)
    relative_path = os.path.join("tutors", str(tutor_id), filename).replace("\\", "/")
    
    return full_path, relative_path


def save_uploaded_file(file, tutor_id: int) -> tuple:
    """
    Save uploaded file and return file info.
    Returns: (file_path, file_name, file_size, mime_type) or None if error
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > config.MAX_FILE_SIZE:
        return None
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename, tutor_id)
    
    # Get upload paths
    full_path, relative_path = get_upload_path(tutor_id, unique_filename)
    
    # Save file
    try:
        file.save(full_path)
        mime_type = file.content_type or 'application/octet-stream'
        return (relative_path, file.filename, file_size, mime_type)
    except Exception as e:
        current_app.logger.error(f"Error saving file: {str(e)}")
        return None


def delete_file(file_path: str) -> bool:
    """Delete a file from the uploads directory."""
    try:
        full_path = os.path.join(config.UPLOAD_DIR, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {str(e)}")
        return False


def get_file_url(file_path: str) -> str:
    """Get URL for accessing a file."""
    # Convert backslashes to forward slashes for URLs
    normalized_path = file_path.replace("\\", "/")
    return f"/uploads/{normalized_path}"

