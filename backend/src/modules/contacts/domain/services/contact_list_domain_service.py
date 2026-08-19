from src.modules.contacts.domain.entities.contact_list_entity import ContactListEntity
from src.modules.contacts.domain.repositories.contact_list_repository import (
    IContactListRepository,
)
from src.shared.exceptions.base_exceptions import (
    ConflictError,
    CreateError,
    DeleteError,
    DomainError,
    NotFoundError,
    ServerError,
    UpdateError,
)


class ContactListDomainService:
    """Domain service for contact list operations."""

    def __init__(self, repository: IContactListRepository):
        self.repository = repository

    async def create(self, entity: ContactListEntity) -> ContactListEntity:
        try:
            await self._ensure_unique_name_in_org(entity.organization_id, entity.name)
            return await self.repository.add(entity)
        except DomainError:
            raise
        except Exception as e:
            raise CreateError(
                error="Failed to create contact list",
                internal_details=str(e),
            ) from e

    async def get_by_uuid(self, list_uuid: str) -> ContactListEntity:
        try:
            entity = await self.repository.get_by(uuid=list_uuid, deleted_at=None)
            if not entity:
                raise NotFoundError(error="Contact list not found")
            return entity
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve contact list",
                internal_details=str(e),
            ) from e

    async def get_by_id(self, list_id: int) -> ContactListEntity | None:
        try:
            return await self.repository.get_by(id=list_id, deleted_at=None)
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve contact list",
                internal_details=str(e),
            ) from e

    async def update(
        self,
        list_uuid: str,
        entity: ContactListEntity,
        existing: ContactListEntity | None = None,
    ) -> ContactListEntity:
        try:
            if existing is None:
                existing = await self.get_by_uuid(list_uuid)
            if existing.id is None:
                raise NotFoundError(error="Contact list not found")
            entity.id = existing.id
            entity.uuid = existing.uuid
            entity.created_at = existing.created_at
            entity.organization_id = existing.organization_id
            if entity.name != existing.name:
                await self._ensure_unique_name_in_org(
                    existing.organization_id,
                    entity.name,
                )
            entity.mark_updated()
            return await self.repository.update(entity)
        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to update contact list",
                internal_details=str(e),
            ) from e

    async def delete(self, list_uuid: str) -> None:
        try:
            existing = await self.get_by_uuid(list_uuid)
            if existing.id is None:
                raise NotFoundError(error="Contact list not found")
            existing.soft_delete()
            await self.repository.update(existing)
        except DomainError:
            raise
        except Exception as e:
            raise DeleteError(
                error="Failed to delete contact list",
                internal_details=str(e),
            ) from e

    async def update_field_definitions(
        self,
        list_entity: ContactListEntity,
        extra_fields: list[str],
    ) -> ContactListEntity:
        """Merge extra CSV columns into the list's field_definitions."""
        try:
            if list_entity.id is None:
                raise NotFoundError(error="Contact list not found")
            existing_extra = set(list_entity.field_definitions or [])
            merged = list(existing_extra | set(extra_fields))
            if merged != list_entity.field_definitions:
                list_entity.field_definitions = merged
                list_entity.mark_updated()
                return await self.repository.update(list_entity)
            return list_entity
        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to update contact list field definitions",
                internal_details=str(e),
            ) from e

    async def list_by_organization(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContactListEntity], int]:
        try:
            return await self.repository.list_by_organization(
                organization_id,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            raise ServerError(
                error="Failed to list contact lists",
                internal_details=str(e),
            ) from e

    async def list_summaries_by_organization(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        try:
            return await self.repository.list_summaries_by_organization(
                organization_id, limit=limit, offset=offset
            )
        except Exception as e:
            raise ServerError(
                error="Failed to list contact collection summaries",
                internal_details=str(e),
            ) from e

    async def _ensure_unique_name_in_org(self, organization_id: int, name: str) -> None:
        existing = await self.repository.get_by(
            organization_id=organization_id,
            name=name,
            deleted_at=None,
        )
        if existing:
            raise ConflictError(
                error="A contact list with this name already exists in your organization",
                errors={"code": "CONTACT_LIST_NAME_EXISTS"},
            )
