from src.modules.auth.domain.repositories.user_activity_repository import IUserActivityRepository
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class ListUserActivitiesUseCase:
    def __init__(self, user_activity_repo: IUserActivityRepository):
        self.user_activity_repo = user_activity_repo

    async def execute(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        try:
            entities, total = await self.user_activity_repo.list_by_user(
                user_id=user_id,
                limit=limit,
                offset=offset,
            )

            items = [
                {
                    "uuid": e.uuid,
                    "activity_type": e.activity_type,
                    "description": e.description,
                    "metadata": e.metadata,
                    "created_at": e.created_at,
                }
                for e in entities
            ]

            return items, total
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while fetching user activities",
                internal_details=str(e),
            ) from e
