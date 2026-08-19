"""Compatibility exports for template asset storage.

Storage adapters are shared infrastructure because profile images, organization
logos, and template assets all use the same provider contract.
"""

from src.shared.infrastructure.storage.cloudinary_uploader import CloudinaryUploader
from src.shared.infrastructure.storage.uploader_interface import UploaderInterface

uploader = CloudinaryUploader()

__all__ = ["CloudinaryUploader", "UploaderInterface", "uploader"]
