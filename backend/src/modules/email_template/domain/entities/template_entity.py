from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.modules.email_template.domain.enums.template_enums import (
    TemplateStatusEnum,
    TemplateTypeEnum,
)
from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin
from src.shared.domain.mixin.soft_delete_mixin import SoftDeleteMixin


@dataclass(kw_only=True)
class TemplateEntity(
    BaseEntity,
    AuditMixin,
    SoftDeleteMixin,
):
    """
    Entity representing a system or organization-owned email template.
    """

    name: str = field(
        metadata={
            "description": "Internal template name",
        }
    )

    subject: str = field(
        metadata={
            "description": (
                "Email subject, which may contain placeholders"
            ),
        }
    )

    body_html: str = field(
        metadata={
            "description": (
                "Rich HTML email body, which may contain placeholders"
            ),
        }
    )

    organization_id: int | None = field(
        default=None,
        metadata={
            "description": "Owning organization id for custom templates",
            "index": True,
            "on_delete": "cascade",
        },
    )

    category_id: int | None = field(
        default=None,
        metadata={
            "description": "Template category id",
            "index": True,
            "on_delete": "set_null",
        },
    )

    source_template_id: int | None = field(
        default=None,
        metadata={
            "description": (
                "Source template id used for copy or duplicate tracking"
            ),
            "index": True,
            "on_delete": "set_null",
        },
    )

    description: str | None = field(
        default=None,
        metadata={
            "description": "Optional template description",
        },
    )

    preheader: str | None = field(
        default=None,
        metadata={
            "description": (
                "Preview text displayed by email clients after the subject"
            ),
        },
    )

    from_name: str | None = field(
        default=None,
        metadata={
            "description": (
                "Optional default sender display name for this template"
            ),
        },
    )

    from_email: str | None = field(
        default=None,
        metadata={
            "description": (
                "Optional default sender email address for this template"
            ),
        },
    )

    tags: list[str] = field(
        default_factory=list,
        metadata={
            "description": (
                "Labels used for organizing and filtering templates"
            ),
        },
    )

    template_type: str = field(
        default=TemplateTypeEnum.CUSTOM.value,
        metadata={
            "description": "Template type such as system or custom",
            "index": True,
        },
    )

    status: str = field(
        default=TemplateStatusEnum.DRAFT.value,
        metadata={
            "description": (
                "Template status such as draft, published, or archived"
            ),
            "index": True,
        },
    )

    is_active: bool = field(
        default=True,
        metadata={
            "description": "Whether the template is active",
            "index": True,
        },
    )

    is_default: bool = field(
        default=False,
        metadata={
            "description": (
                "Whether this is the organization's default template"
            ),
            "index": True,
        },
    )

    smart_personalization_enabled: bool = field(
        default=False,
        metadata={
            "description": (
                "Whether smart personalization is enabled for this template"
            ),
        },
    )

    published_at: datetime | None = field(
        default=None,
        metadata={
            "description": "Date and time when the template was published",
        },
    )

    archived_at: datetime | None = field(
        default=None,
        metadata={
            "description": "Date and time when the template was archived",
        },
    )

    def is_system(self) -> bool:
        """
        Returns True if this is a global system template.
        """
        return self.template_type == TemplateTypeEnum.SYSTEM.value

    def is_custom(self) -> bool:
        """
        Returns True if this is an organization-owned custom template.
        """
        return self.template_type == TemplateTypeEnum.CUSTOM.value

    def is_draft(self) -> bool:
        """
        Returns True if template status is draft.
        """
        return self.status == TemplateStatusEnum.DRAFT.value

    def is_published(self) -> bool:
        """
        Returns True if template status is published.
        """
        return self.status == TemplateStatusEnum.PUBLISHED.value

    def is_archived(self) -> bool:
        """
        Returns True if template status is archived.
        """
        return self.status == TemplateStatusEnum.ARCHIVED.value

    def publish(self) -> None:
        """
        Publishes the template.
        """
        self.status = TemplateStatusEnum.PUBLISHED.value
        self.published_at = datetime.now(UTC)
        self.archived_at = None
        self.mark_updated()

    def archive(self) -> None:
        """
        Archives the template.
        """
        self.status = TemplateStatusEnum.ARCHIVED.value
        self.archived_at = datetime.now(UTC)
        self.mark_updated()