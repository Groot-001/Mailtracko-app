from dataclasses import dataclass, field
from datetime import datetime

from src.shared.domain.entity.base_entity import BaseEntity


@dataclass(kw_only=True)
class SmtpConfigEntity(BaseEntity):
    encrypted_password: str = field(metadata={"description": "Fernet-encrypted SMTP password"})
    smtp_host: str = field(metadata={"description": "SMTP server hostname"})
    smtp_port: int = field(metadata={"description": "SMTP server port"})
    smtp_username: str = field(metadata={"description": "SMTP username"})
    imap_host: str | None = field(default=None, metadata={"description": "IMAP server hostname"})
    imap_port: int | None = field(default=None, metadata={"description": "IMAP server port"})
    verification_code_hash: str | None = field(default=None, metadata={"description": "SHA-256 hash of verification code"})
    verification_sent_at: datetime | None = field(default=None, metadata={"description": "When verification code was sent"})
    verification_attempts: int = field(default=0, metadata={"description": "How many times code was resent"})
    code_expires_at: datetime | None = field(default=None, metadata={"description": "When verification code expires"})