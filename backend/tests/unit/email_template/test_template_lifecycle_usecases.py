# Test compatibility update: use the current src.modules package path; production logic is unchanged.
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest


def _make_template(**overrides):
    from src.modules.email_template.domain.entities.template_entity import (
        TemplateEntity,
    )

    data = {
        "id": 1,
        "uuid": "template-uuid",
        "organization_id": 1,
        "category_id": 2,
        "source_template_id": None,
        "name": "Welcome Template",
        "description": "Welcome email for new contacts",
        "subject": "Welcome {{first_name}}",
        "body_html": "<p>Hello {{first_name}}</p>",
        "template_type": "custom",
        "status": "draft",
        "is_active": True,
        "created_by_id": 10,
        "updated_by_id": None,
    }

    data.update(overrides)
    return TemplateEntity(**data)


def _make_duplicate_payload(**overrides):
    from src.modules.email_template.presentation.schemas.template_schemas import (
        DuplicateTemplateRequestSchema,
    )

    return DuplicateTemplateRequestSchema(**overrides)


def _get_first_awaited_argument(mock: AsyncMock) -> Any:
    """
    Returns the first positional argument from the latest awaited mock call.

    The explicit assertion also informs Pylance that await_args is not None.
    """
    awaited_call = mock.await_args
    assert awaited_call is not None

    return awaited_call.args[0]


# ------------------------------------------------ Publish Template ------------------------------------------------ #


@pytest.mark.asyncio
async def test_publish_template_usecase_success():
    from src.modules.email_template.application.usecases.lifecycle.publish_template_usecase import (
        PublishTemplateUseCase,
    )
    from src.modules.email_template.domain.events.template_domain_events import (
        TemplatePublishedEvent,
    )

    source_template = _make_template(
        status="draft",
    )
    published_template = _make_template(
        status="published",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.publish_custom_template = AsyncMock(
        return_value=published_template
    )

    usecase = PublishTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "publish_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            template_uuid="template-uuid",
            organization_id=1,
            actor_id=10,
        )

    assert result == published_template
    assert result.status == "published"

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="template-uuid",
        organization_id=1,
    )
    mock_template_service.publish_custom_template.assert_awaited_once_with(
        template_id=1,
        organization_id=1,
        actor_id=10,
    )

    mock_publish.assert_awaited_once()

    published_event = _get_first_awaited_argument(mock_publish)

    assert isinstance(
        published_event,
        TemplatePublishedEvent,
    )
    assert published_event.template_id == 1
    assert published_event.template_uuid == "template-uuid"
    assert published_event.organization_id == 1
    assert published_event.published_by_id == 10


@pytest.mark.asyncio
async def test_publish_template_usecase_raises_when_template_not_found():
    from src.modules.email_template.application.usecases.lifecycle.publish_template_usecase import (
        PublishTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=None
    )
    mock_template_service.publish_custom_template = AsyncMock()

    usecase = PublishTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "publish_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(ServerError):
            await usecase.execute(
                template_uuid="missing-template-uuid",
                organization_id=1,
                actor_id=10,
            )

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="missing-template-uuid",
        organization_id=1,
    )
    mock_template_service.publish_custom_template.assert_not_awaited()
    mock_publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_publish_template_usecase_raises_when_source_template_has_no_id():
    from src.modules.email_template.application.usecases.lifecycle.publish_template_usecase import (
        PublishTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    source_template = _make_template(
        id=None,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.publish_custom_template = AsyncMock()

    usecase = PublishTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="template-uuid",
            organization_id=1,
            actor_id=10,
        )

    mock_template_service.publish_custom_template.assert_not_awaited()


@pytest.mark.asyncio
async def test_publish_template_usecase_raises_when_published_template_has_no_id():
    from src.modules.email_template.application.usecases.lifecycle.publish_template_usecase import (
        PublishTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    source_template = _make_template()

    published_template = _make_template(
        id=None,
        status="published",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.publish_custom_template = AsyncMock(
        return_value=published_template
    )

    usecase = PublishTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "publish_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(ServerError):
            await usecase.execute(
                template_uuid="template-uuid",
                organization_id=1,
                actor_id=10,
            )

    mock_template_service.publish_custom_template.assert_awaited_once_with(
        template_id=1,
        organization_id=1,
        actor_id=10,
    )
    mock_publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_publish_template_usecase_preserves_domain_error():
    from src.modules.email_template.application.usecases.lifecycle.publish_template_usecase import (
        PublishTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    source_template = _make_template()

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.publish_custom_template = AsyncMock(
        side_effect=InvalidError(
            error="Only draft templates can be published",
        )
    )

    usecase = PublishTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(InvalidError):
        await usecase.execute(
            template_uuid="template-uuid",
            organization_id=1,
            actor_id=10,
        )


# ------------------------------------------------ Archive Template ------------------------------------------------ #


@pytest.mark.asyncio
async def test_archive_template_usecase_success():
    from src.modules.email_template.application.usecases.lifecycle.archive_template_usecase import (
        ArchiveTemplateUseCase,
    )
    from src.modules.email_template.domain.events.template_domain_events import (
        TemplateArchivedEvent,
    )

    source_template = _make_template(
        status="published",
    )
    archived_template = _make_template(
        status="archived",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.archive_custom_template = AsyncMock(
        return_value=archived_template
    )

    usecase = ArchiveTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "archive_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            template_uuid="template-uuid",
            organization_id=1,
            actor_id=10,
        )

    assert result == archived_template
    assert result.status == "archived"

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="template-uuid",
        organization_id=1,
    )
    mock_template_service.archive_custom_template.assert_awaited_once_with(
        template_id=1,
        organization_id=1,
        actor_id=10,
    )

    mock_publish.assert_awaited_once()

    archived_event = _get_first_awaited_argument(mock_publish)

    assert isinstance(
        archived_event,
        TemplateArchivedEvent,
    )
    assert archived_event.template_id == 1
    assert archived_event.template_uuid == "template-uuid"
    assert archived_event.organization_id == 1
    assert archived_event.archived_by_id == 10


@pytest.mark.asyncio
async def test_archive_template_usecase_raises_when_template_not_found():
    from src.modules.email_template.application.usecases.lifecycle.archive_template_usecase import (
        ArchiveTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=None
    )
    mock_template_service.archive_custom_template = AsyncMock()

    usecase = ArchiveTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "archive_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(ServerError):
            await usecase.execute(
                template_uuid="missing-template-uuid",
                organization_id=1,
                actor_id=10,
            )

    mock_template_service.archive_custom_template.assert_not_awaited()
    mock_publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_archive_template_usecase_raises_when_source_template_has_no_id():
    from src.modules.email_template.application.usecases.lifecycle.archive_template_usecase import (
        ArchiveTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    source_template = _make_template(
        id=None,
        status="published",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.archive_custom_template = AsyncMock()

    usecase = ArchiveTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="template-uuid",
            organization_id=1,
            actor_id=10,
        )

    mock_template_service.archive_custom_template.assert_not_awaited()


@pytest.mark.asyncio
async def test_archive_template_usecase_raises_when_archived_template_has_no_id():
    from src.modules.email_template.application.usecases.lifecycle.archive_template_usecase import (
        ArchiveTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    source_template = _make_template(
        status="published",
    )
    archived_template = _make_template(
        id=None,
        status="archived",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.archive_custom_template = AsyncMock(
        return_value=archived_template
    )

    usecase = ArchiveTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "archive_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(ServerError):
            await usecase.execute(
                template_uuid="template-uuid",
                organization_id=1,
                actor_id=10,
            )

    mock_template_service.archive_custom_template.assert_awaited_once_with(
        template_id=1,
        organization_id=1,
        actor_id=10,
    )
    mock_publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_archive_template_usecase_preserves_domain_error():
    from src.modules.email_template.application.usecases.lifecycle.archive_template_usecase import (
        ArchiveTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    source_template = _make_template(
        status="draft",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.archive_custom_template = AsyncMock(
        side_effect=InvalidError(
            error="Only published templates can be archived",
        )
    )

    usecase = ArchiveTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(InvalidError):
        await usecase.execute(
            template_uuid="template-uuid",
            organization_id=1,
            actor_id=10,
        )


# ------------------------------------------------ Restore Template ------------------------------------------------ #


@pytest.mark.asyncio
async def test_restore_template_usecase_success():
    from src.modules.email_template.application.usecases.lifecycle.restore_template_usecase import (
        RestoreTemplateUseCase,
    )
    from src.modules.email_template.domain.events.template_domain_events import (
        TemplateRestoredEvent,
    )

    source_template = _make_template(
        status="archived",
    )
    restored_template = _make_template(
        status="draft",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.restore_custom_template = AsyncMock(
        return_value=restored_template
    )

    usecase = RestoreTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "restore_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            template_uuid="template-uuid",
            organization_id=1,
            actor_id=10,
        )

    assert result == restored_template
    assert result.status == "draft"

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="template-uuid",
        organization_id=1,
    )
    mock_template_service.restore_custom_template.assert_awaited_once_with(
        template_id=1,
        organization_id=1,
        actor_id=10,
    )

    mock_publish.assert_awaited_once()

    restored_event = _get_first_awaited_argument(mock_publish)

    assert isinstance(
        restored_event,
        TemplateRestoredEvent,
    )
    assert restored_event.template_id == 1
    assert restored_event.template_uuid == "template-uuid"
    assert restored_event.organization_id == 1
    assert restored_event.restored_by_id == 10


@pytest.mark.asyncio
async def test_restore_template_usecase_raises_when_template_not_found():
    from src.modules.email_template.application.usecases.lifecycle.restore_template_usecase import (
        RestoreTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=None
    )
    mock_template_service.restore_custom_template = AsyncMock()

    usecase = RestoreTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "restore_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(ServerError):
            await usecase.execute(
                template_uuid="missing-template-uuid",
                organization_id=1,
                actor_id=10,
            )

    mock_template_service.restore_custom_template.assert_not_awaited()
    mock_publish.assert_not_awaited()


# ------------------------------------------------ Duplicate Template ------------------------------------------------ #


@pytest.mark.asyncio
async def test_duplicate_template_usecase_success_with_default_name():
    from src.modules.email_template.application.usecases.lifecycle.duplicate_template_usecase import (
        DuplicateTemplateUseCase,
    )
    from src.modules.email_template.domain.events.template_domain_events import (
        TemplateDuplicatedEvent,
    )

    source_template = _make_template(
        id=5,
        uuid="source-template-uuid",
        name="Sales Introduction",
        status="published",
    )

    duplicated_template = _make_template(
        id=6,
        uuid="duplicated-template-uuid",
        source_template_id=5,
        name="Sales Introduction Copy",
        status="draft",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.create_custom_template = AsyncMock(
        return_value=duplicated_template
    )

    usecase = DuplicateTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "duplicate_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            template_uuid="source-template-uuid",
            payload=_make_duplicate_payload(),
            organization_id=1,
            actor_id=10,
        )

    assert result == duplicated_template
    assert result.status == "draft"
    assert result.source_template_id == 5
    assert result.name == "Sales Introduction Copy"

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="source-template-uuid",
        organization_id=1,
    )
    mock_template_service.create_custom_template.assert_awaited_once()

    duplicated_entity = _get_first_awaited_argument(
        mock_template_service.create_custom_template
    )

    assert duplicated_entity.organization_id == 1
    assert duplicated_entity.category_id == 2
    assert duplicated_entity.source_template_id == 5
    assert duplicated_entity.name == "Sales Introduction Copy"
    assert duplicated_entity.description == "Welcome email for new contacts"
    assert duplicated_entity.subject == "Welcome {{first_name}}"
    assert duplicated_entity.body_html == "<p>Hello {{first_name}}</p>"
    assert duplicated_entity.template_type == "custom"
    assert duplicated_entity.status == "draft"
    assert duplicated_entity.created_by_id == 10

    mock_publish.assert_awaited_once()

    duplicated_event = _get_first_awaited_argument(mock_publish)

    assert isinstance(
        duplicated_event,
        TemplateDuplicatedEvent,
    )
    assert duplicated_event.template_id == 6
    assert duplicated_event.template_uuid == "duplicated-template-uuid"
    assert duplicated_event.source_template_id == 5
    assert duplicated_event.organization_id == 1
    assert duplicated_event.duplicated_by_id == 10


@pytest.mark.asyncio
async def test_duplicate_template_usecase_success_with_custom_name():
    from src.modules.email_template.application.usecases.lifecycle.duplicate_template_usecase import (
        DuplicateTemplateUseCase,
    )

    source_template = _make_template(
        id=5,
        uuid="source-template-uuid",
        name="Sales Introduction",
    )
    duplicated_template = _make_template(
        id=6,
        uuid="duplicated-template-uuid",
        source_template_id=5,
        name="My Sales Template",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.create_custom_template = AsyncMock(
        return_value=duplicated_template
    )

    usecase = DuplicateTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "duplicate_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ):
        result = await usecase.execute(
            template_uuid="source-template-uuid",
            payload=_make_duplicate_payload(
                name="My Sales Template",
            ),
            organization_id=1,
            actor_id=10,
        )

    assert result == duplicated_template

    duplicated_entity = _get_first_awaited_argument(
        mock_template_service.create_custom_template
    )

    assert duplicated_entity.name == "My Sales Template"
    assert duplicated_entity.source_template_id == 5
    assert duplicated_entity.status == "draft"


@pytest.mark.asyncio
async def test_duplicate_template_usecase_preserves_html_and_placeholders():
    from src.modules.email_template.application.usecases.lifecycle.duplicate_template_usecase import (
        DuplicateTemplateUseCase,
    )

    source_template = _make_template(
        id=5,
        uuid="source-template-uuid",
        subject="Hello {{first_name}} from {{company}}",
        body_html=(
            '<p>Hello {{first_name}}</p>'
            '<a href="https://example.com">Open link</a>'
            '<img src="https://cdn.example.com/image.png">'
            "<button>Get Started</button>"
        ),
    )

    duplicated_template = _make_template(
        id=6,
        uuid="duplicated-template-uuid",
        source_template_id=5,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.create_custom_template = AsyncMock(
        return_value=duplicated_template
    )

    usecase = DuplicateTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "duplicate_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ):
        await usecase.execute(
            template_uuid="source-template-uuid",
            payload=_make_duplicate_payload(),
            organization_id=1,
            actor_id=10,
        )

    duplicated_entity = _get_first_awaited_argument(
        mock_template_service.create_custom_template
    )

    assert duplicated_entity.subject == (
        "Hello {{first_name}} from {{company}}"
    )
    assert duplicated_entity.body_html == source_template.body_html
    assert "{{first_name}}" in duplicated_entity.body_html
    assert "https://example.com" in duplicated_entity.body_html
    assert (
        "https://cdn.example.com/image.png"
        in duplicated_entity.body_html
    )
    assert "<button>Get Started</button>" in duplicated_entity.body_html


@pytest.mark.asyncio
async def test_duplicate_template_usecase_raises_when_source_not_found():
    from src.modules.email_template.application.usecases.lifecycle.duplicate_template_usecase import (
        DuplicateTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=None
    )
    mock_template_service.create_custom_template = AsyncMock()

    usecase = DuplicateTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "duplicate_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(CreateError):
            await usecase.execute(
                template_uuid="missing-template-uuid",
                payload=_make_duplicate_payload(),
                organization_id=1,
                actor_id=10,
            )

    mock_template_service.create_custom_template.assert_not_awaited()
    mock_publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_template_usecase_raises_when_source_has_no_id():
    from src.modules.email_template.application.usecases.lifecycle.duplicate_template_usecase import (
        DuplicateTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    source_template = _make_template(
        id=None,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.create_custom_template = AsyncMock()

    usecase = DuplicateTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(CreateError):
        await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_duplicate_payload(),
            organization_id=1,
            actor_id=10,
        )

    mock_template_service.create_custom_template.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_template_usecase_raises_when_created_template_has_no_id():
    from src.modules.email_template.application.usecases.lifecycle.duplicate_template_usecase import (
        DuplicateTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    source_template = _make_template(
        id=5,
    )
    duplicated_template = _make_template(
        id=None,
        source_template_id=5,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.create_custom_template = AsyncMock(
        return_value=duplicated_template
    )

    usecase = DuplicateTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.lifecycle."
        "duplicate_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(CreateError):
            await usecase.execute(
                template_uuid="template-uuid",
                payload=_make_duplicate_payload(),
                organization_id=1,
                actor_id=10,
            )

    mock_template_service.create_custom_template.assert_awaited_once()
    mock_publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_template_usecase_preserves_domain_error():
    from src.modules.email_template.application.usecases.lifecycle.duplicate_template_usecase import (
        DuplicateTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        side_effect=InvalidError(
            error="Template does not belong to this organization",
        )
    )

    usecase = DuplicateTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(InvalidError):
        await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_duplicate_payload(),
            organization_id=999,
            actor_id=10,
        )