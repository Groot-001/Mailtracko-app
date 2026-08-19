
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.email_account.domain.entities.smtp_config_entity import SmtpConfigEntity
from src.modules.email_account.domain.repositories.smtp_config_repository import ISmtpConfigRepository
from src.shared.infrastructure.repository.base_repository import BaseRepository


class SmtpConfigRepositoryImpl(BaseRepository[SmtpConfigEntity], ISmtpConfigRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session, table_name="email_smtp_configs")

    def to_row(self, entity: SmtpConfigEntity) -> dict:
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "encrypted_password": entity.encrypted_password,
            "smtp_host": entity.smtp_host,
            "smtp_port": entity.smtp_port,
            "smtp_username": entity.smtp_username,
            "imap_host": entity.imap_host,
            "imap_port": entity.imap_port,
            "verification_code_hash": entity.verification_code_hash,
            "verification_sent_at": entity.verification_sent_at,
            "verification_attempts": entity.verification_attempts,
            "code_expires_at": entity.code_expires_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> SmtpConfigEntity:
        return SmtpConfigEntity(
            id=row.get("id"),
            uuid=row["uuid"],
            encrypted_password=row["encrypted_password"],
            smtp_host=row["smtp_host"],
            smtp_port=row["smtp_port"],
            smtp_username=row["smtp_username"],
            imap_host=row.get("imap_host"),
            imap_port=row.get("imap_port"),
            verification_code_hash=row.get("verification_code_hash"),
            verification_sent_at=row.get("verification_sent_at"),
            verification_attempts=row.get("verification_attempts", 0),
            code_expires_at=row.get("code_expires_at"),
            created_at=row["created_at"],
            updated_at=row.get("updated_at"),
        )