from dataclasses import dataclass, field

from src.modules.email_template.domain.enums.template_enums import (
    TemplateAssetTypeEnum,
    TemplateAssetUsageEnum,
)
from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin
from src.shared.domain.mixin.soft_delete_mixin import SoftDeleteMixin


@dataclass(kw_only=True)
class TemplateAssetEntity(BaseEntity, AuditMixin, SoftDeleteMixin):
    """
    Entity representing an inline image or downloadable template attachment.
    """

    template_id: int = field(
        metadata={
            "description": "Template id associated with the uploaded asset",
            "index": True,
            "on_delete": "cascade",
        }
    )

    original_filename: str = field(
        metadata={
            "description": "Original filename provided during upload",
        }
    )

    storage_key: str = field(
        metadata={
            "description": "Unique storage provider key for the asset",
            "unique": True,
            "index": True,
        }
    )

    file_url: str = field(
        metadata={
            "description": "URL used to access the uploaded asset",
        }
    )

    content_type: str = field(
        metadata={
            "description": "MIME content type of the uploaded asset",
        }
    )

    file_size: int = field(
        metadata={
            "description": "Uploaded asset size in bytes",
        }
    )

    asset_type: str = field(
        metadata={
            "description": "Asset type such as image or document",
            "index": True,
        }
    )

    usage: str = field(
        metadata={
            "description": "Asset usage such as inline or attachment",
            "index": True,
        }
    )

    organization_id: int | None = field(
        default=None,
        metadata={
            "description": "Organization id that owns the uploaded asset",
            "index": True,
            "on_delete": "cascade",
        },
    )

    uploaded_by_id: int | None = field(
        default=None,
        metadata={
            "description": "User id who uploaded the asset",
            "index": True,
            "on_delete": "set_null",
        },
    )

    is_active: bool = field(
        default=True,
        metadata={
            "description": "Whether the uploaded asset is active",
        },
    )

    def is_image(self) -> bool:
        """
        Returns True if the asset is an image.
        """
        return self.asset_type == TemplateAssetTypeEnum.IMAGE.value

    def is_document(self) -> bool:
        """
        Returns True if the asset is a document.
        """
        return self.asset_type == TemplateAssetTypeEnum.DOCUMENT.value

    def is_inline(self) -> bool:
        """
        Returns True if the asset is used inside the email body.
        """
        return self.usage == TemplateAssetUsageEnum.INLINE.value

    def is_attachment(self) -> bool:
        """
        Returns True if the asset is a downloadable email attachment.
        """
        return self.usage == TemplateAssetUsageEnum.ATTACHMENT.value

    def has_valid_inline_usage(self) -> bool:
        """
        Returns True if inline usage is assigned only to an image.
        """
        return not self.is_inline() or self.is_image()