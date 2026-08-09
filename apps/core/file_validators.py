import os
from django.core.exceptions import ValidationError


ALLOWED_UPLOAD_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".pdf", ".doc", ".docx",
    ".ppt", ".pptx", ".xls", ".xlsx", ".csv", ".txt",
}


def validate_safe_file_extension(file):
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValidationError(
            "Unsupported file type. Please upload a safe document or image file."
        )