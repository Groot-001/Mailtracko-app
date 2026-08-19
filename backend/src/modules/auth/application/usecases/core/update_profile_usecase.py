from src.modules.auth.domain.entities.user_activity_entity import UserActivityEntity
from src.modules.auth.domain.enums.user_activity_enums import UserActivityTypeEnum
from src.modules.auth.domain.events.auth_domain_events import UserUpdatedEvent
from src.modules.auth.domain.repositories.user_activity_repository import IUserActivityRepository
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError
from src.shared.mediator.mediator import mediator


class UpdateProfileUseCase:
    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_activity_repo: IUserActivityRepository,
    ):
        self.user_domain_service = user_domain_service
        self.user_activity_repo = user_activity_repo

    async def execute(
        self,
        user_id: int,
        full_name: str | None = None,
        theme: str | None = None,
        profile_image: str | None = None,
        timezone: str | None = None,
        phone: str | None = None,
        country_code: str | None = None,
        location: str | None = None,
    ) -> dict:
        try:
            user = await self.user_domain_service.get_active_user_by_id(user_id)
            if not user:
                raise InvalidError(error="User not found")

            if full_name is not None:
                user.full_name = full_name
            if profile_image is not None:
                user.profile_image = profile_image
            if timezone is not None:
                user.timezone = timezone
            if phone is not None:
                user.phone = phone
            if country_code is not None:
                user.country_code = country_code
            if location is not None:
                user.location = location
            if theme is not None:
                valid_themes = {"light", "dark"}
                if theme not in valid_themes:
                    raise InvalidError(error=f"Theme must be one of: {', '.join(valid_themes)}")
                user.theme = theme

            user.mark_updated()
            updated = await self.user_domain_service.update_user(user)

            changed = {}
            if full_name is not None:
                changed["full_name"] = full_name
            if profile_image is not None:
                changed["profile_image"] = True
            if timezone is not None:
                changed["timezone"] = timezone
            if phone is not None:
                changed["phone"] = True
            if country_code is not None:
                changed["country_code"] = country_code
            if location is not None:
                changed["location"] = location
            if theme is not None:
                changed["theme"] = theme
            updated.add_event(
                UserUpdatedEvent(user_id=user_id, value=str(changed) if changed else None)
            )
            for event in updated.pull_events():
                await mediator.publish(event)

            changed_fields = [k for k in changed.keys()]
            if changed_fields:
                activity = UserActivityEntity(
                    user_id=user_id,
                    activity_type=UserActivityTypeEnum.PROFILE_UPDATED.value,
                    description=f"Profile updated: {', '.join(changed_fields)}",
                    metadata={"changed_fields": changed_fields},
                )
                await self.user_activity_repo.add(activity)

            return {
                "uuid": updated.uuid,
                "full_name": updated.full_name,
                "email": updated.email,
                "profile_image": updated.profile_image,
                "timezone": updated.timezone,
                "phone": updated.phone,
                "country_code": updated.country_code,
                "location": updated.location,
                "theme": updated.theme,
                "created_at": updated.created_at.isoformat() if updated.created_at else None,
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to update profile", internal_details=str(e)) from e
