"""
Validators for the statements app
"""

import os
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_file_extension(value):
    """
    Validate that the uploaded file has an allowed extension.

    Args:
        value: File object

    Raises:
        ValidationError: If file extension is not allowed
    """
    ext = os.path.splitext(value.name)[1].lower()
    allowed_extensions = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', ['.csv', '.xlsx', '.xls', '.pdf', '.txt'])

    if ext not in allowed_extensions:
        raise ValidationError(
            f'Unsupported file extension {ext}. Allowed extensions are: {", ".join(allowed_extensions)}'
        )


def validate_file_size(value):
    """
    Validate that the uploaded file is not too large.

    Args:
        value: File object

    Raises:
        ValidationError: If file size exceeds limit
    """
    max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 10485760)  # 10 MB default

    if value.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(f'File size cannot exceed {max_size_mb:.1f} MB')
