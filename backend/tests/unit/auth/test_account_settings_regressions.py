from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.auth.application.usecases.core.change_password_usecase import ChangePasswordUseCase
from src.modules.auth.application.usecases.core.update_profile_usecase import UpdateProfileUseCase
from src.modules.auth.application.usecases.session.revoke_other_sessions_usecase import RevokeOtherSessionsUseCase
from src.modules.auth.domain.entities.user_entity import UserEntity
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.shared.exceptions.base_exceptions import InvalidError


@pytest.mark.parametrize(
    "password",
    [
        "Short1!",
        f"ValidPassword1!{'x' * 114}",
        "lowercaseonly1!",
        "UPPERCASEONLY1!",
        "MissingNumber!",
        "MissingSymbol1",
    ],
)
def test_password_policy_rejects_invalid_values(password: str) -> None:
    service = UserDomainService(repository=MagicMock(), hasher_service=MagicMock())
    with pytest.raises(InvalidError):
        service.validate_password(password)


def test_password_policy_accepts_12_to_128_character_passwords() -> None:
    service = UserDomainService(repository=MagicMock(), hasher_service=MagicMock())
    assert service.validate_password("ValidPass1!x") == "ValidPass1!x"
    max_length_password = "Aa1!" + ("x" * 124)
    assert service.validate_password(max_length_password) == max_length_password


@pytest.mark.asyncio
async def test_profile_update_can_clear_photo_and_save_dark_theme(monkeypatch) -> None:
    user = UserEntity(
        id=7,
        uuid="user-uuid",
        full_name="MailTracko User",
        email="user@example.com",
        profile_image="https://example.com/old-photo.png",
        theme="light",
    )
    user_domain_service = MagicMock()
    user_domain_service.get_active_user_by_id = AsyncMock(return_value=user)
    user_domain_service.update_user = AsyncMock(return_value=user)
    activity_repo = MagicMock()
    activity_repo.add = AsyncMock()
    publish = AsyncMock()
    monkeypatch.setattr(
        "src.modules.auth.application.usecases.core.update_profile_usecase.mediator.publish",
        publish,
    )

    result = await UpdateProfileUseCase(
        user_domain_service=user_domain_service,
        user_activity_repo=activity_repo,
    ).execute(user_id=7, profile_image="", theme="dark")

    assert result["profile_image"] == ""
    assert result["theme"] == "dark"
    user_domain_service.update_user.assert_awaited_once_with(user)
    activity_repo.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_revoke_other_sessions_is_one_atomic_service_call() -> None:
    session_service = MagicMock()
    session_service.revoke_all_except_current = AsyncMock()

    await RevokeOtherSessionsUseCase(session_service).execute(
        user_id=7,
        current_session_uuid="current-session",
    )

    session_service.revoke_all_except_current.assert_awaited_once_with(
        user_id=7,
        current_session_uuid="current-session",
    )


@pytest.mark.asyncio
async def test_revoke_other_sessions_requires_current_session() -> None:
    session_service = MagicMock()
    with pytest.raises(InvalidError):
        await RevokeOtherSessionsUseCase(session_service).execute(
            user_id=7,
            current_session_uuid=None,
        )


@pytest.mark.asyncio
async def test_password_change_fallback_revokes_all_sessions() -> None:
    account = MagicMock(hashed_password="old-hash")
    user_domain_service = MagicMock()
    user_domain_service.verify_password.return_value = True
    user_domain_service.validate_password.return_value = "ValidPass1!x"
    user_domain_service.get_active_user_by_id = AsyncMock(return_value=None)
    account_service = MagicMock()
    account_service.get_user_account_by_user_id = AsyncMock(return_value=account)
    account_service.update_user_account = AsyncMock(return_value=account)
    session_service = MagicMock()
    session_service.revoke_all_sessions_for_user = AsyncMock(return_value=[])
    hasher_service = MagicMock()
    hasher_service.hash.return_value = "new-hash"
    activity_repo = MagicMock()
    activity_repo.add = AsyncMock()

    result = await ChangePasswordUseCase(
        user_domain_service=user_domain_service,
        user_account_domain_service=account_service,
        user_session_domain_service=session_service,
        hasher_service=hasher_service,
        user_activity_repo=activity_repo,
    ).execute(
        user_id=7,
        current_password="OldPassword1!",
        new_password="ValidPass1!x",
        confirm_password="ValidPass1!x",
        current_session_uuid=None,
    )

    assert result == {"message": "Password changed successfully"}
    session_service.revoke_all_sessions_for_user.assert_awaited_once_with(user_id=7)


@pytest.mark.asyncio
async def test_current_user_reports_enabled_2fa_state() -> None:
    from src.modules.auth.application.usecases.core.get_current_user_usecase import GetCurrentUserUseCase
    from src.modules.auth.domain.entities.user_totp_secret_entity import UserTotpSecretEntity
    from src.modules.auth.presentation.schemas.auth_schemas import UserResponse

    user = UserEntity(
        id=7,
        uuid="user-uuid",
        full_name="MailTracko User",
        email="user@example.com",
        theme="light",
    )
    user_domain_service = MagicMock()
    user_domain_service.get_active_user_by_id = AsyncMock(return_value=user)
    member_service = MagicMock()
    member_service.get_active_member_by_user_id = AsyncMock(return_value=None)
    organization_service = MagicMock()
    totp_repo = MagicMock()
    totp_repo.get_by = AsyncMock(
        return_value=UserTotpSecretEntity(user_id=7, secret="encrypted-secret", enabled=True)
    )

    result = await GetCurrentUserUseCase(
        user_domain_service=user_domain_service,
        organization_member_domain_service=member_service,
        organization_domain_service=organization_service,
        totp_repo=totp_repo,
    ).execute(user_id=7)

    assert result["is_2fa_enabled"] is True
    user_fields = {key: value for key, value in result.items() if key in UserResponse.model_fields}
    assert UserResponse(**user_fields).is_2fa_enabled is True
    totp_repo.get_by.assert_awaited_once_with(user_id=7)
