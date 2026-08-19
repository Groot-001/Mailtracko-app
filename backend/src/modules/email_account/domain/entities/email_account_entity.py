from dataclasses import dataclass, field
from datetime import UTC, datetime, date

from src.modules.email_account.domain.enums.email_account_enums import (
    EmailAccountProvider,
    EmailAccountStatus,
    EmailAccountHealthStatus,
)
from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin
from src.shared.domain.mixin.soft_delete_mixin import SoftDeleteMixin


@dataclass(kw_only=True)
class EmailAccountEntity(BaseEntity, AuditMixin, SoftDeleteMixin):
    organization_id: int = field(metadata={"description": "FK to org_organizations.id"})
    provider: str = field(metadata={"description": "Email provider"})
    email: str = field(metadata={"description": "Email address of the account"})
    sender_name: str | None = field(default=None, metadata={"description": "Display name used in From header"})
    status: str = field(default=EmailAccountStatus.PENDING_VERIFICATION.value, metadata={"description": "Current status of the email account"})
    smtp_config_id: int | None = field(default=None, metadata={"description": "FK to email_smtp_configs.id"})
    oauth_config_id: int | None = field(default=None, metadata={"description": "FK to email_oauth_configs.id"})
    health_status: str = field(default=EmailAccountHealthStatus.UNKNOWN.value, metadata={"description": "Health check status"})
    daily_sent_count: int = field(default=0, metadata={"description": "Emails sent today"})
    last_sent_date: date | None = field(default=None, metadata={"description": "Date of last sent email (UTC)"})
    sending_limit: int = field(default=100, metadata={"description": "Max emails per day"})
    reply_to: str | None = field(default=None, metadata={"description": "Default reply-to address"})
    signature: str | None = field(default=None, metadata={"description": "Default email signature (HTML)"})
    last_used_at: datetime | None = field(default=None, metadata={"description": "When the account was last used to send"})
    health_score: int | None = field(default=None, metadata={"description": "Overall health score 0-100"})
    health_details: dict | None = field(default=None, metadata={"description": "Detailed health check breakdown"})

    def is_active(self) -> bool:
        return self.status == EmailAccountStatus.ACTIVE.value

    def is_pending_verification(self) -> bool:
        return self.status == EmailAccountStatus.PENDING_VERIFICATION.value

    def mark_active(self) -> None:
        self.status = EmailAccountStatus.ACTIVE.value
        self.mark_updated()

    def mark_reconnect_required(self) -> None:
        self.status = EmailAccountStatus.RECONNECT_REQUIRED.value
        self.mark_updated()

    def mark_disconnected(self) -> None:
        self.status = EmailAccountStatus.DISCONNECTED.value
        self.mark_updated()

    def reset_daily_if_new_day(self) -> None:
        today = datetime.now(UTC).date()
        if self.last_sent_date != today:
            self.daily_sent_count = 0
            self.last_sent_date = today

    def can_send(self) -> bool:
        return (
            self.is_active()
            and self.health_status != EmailAccountHealthStatus.UNHEALTHY.value
            and self.daily_sent_count < self.sending_limit
        )

    def is_oauth(self) -> bool:
        return self.provider == EmailAccountProvider.GMAIL.value