# Test compatibility update: use the current src.modules package path; production logic is unchanged.
from unittest.mock import AsyncMock, patch

import pytest


def _make_template(**overrides):
    from src.modules.email_template.domain.entities.template_entity import (
        TemplateEntity,
    )

    data = {
        "id": 1,
        "uuid": "template-uuid",
        "organization_id": None,
        "category_id": 2,
        "source_template_id": None,
        "name": "System Welcome Template",
        "description": "System welcome email",
        "subject": "Welcome {{first_name}}",
        "body_html": (
            '<p>Hello {{first_name}}</p>'
            '<a href="https://example.com">Open</a>'
            '<img src="https://cdn.example.com/welcome.png">'
            "<button>Get Started</button>"
        ),
        "template_type": "system",
        "status": "published",
        "is_active": True,
        "created_by_id": 1,
        "updated_by_id": None,
    }

    data.update(overrides)

    return TemplateEntity(**data)


def _make_category(**overrides):
    from src.modules.email_template.domain.entities.template_category_entity import (
        TemplateCategoryEntity,
    )

    data = {
        "id": 1,
        "uuid": "category-uuid",
        "name": "Welcome",
        "description": "Welcome email templates",
        "display_order": 1,
        "is_active": True,
        "created_by_id": 1,
        "updated_by_id": None,
    }

    data.update(overrides)

    return TemplateCategoryEntity(**data)


## -------------------------------- Categories -------------------------------- ##


@pytest.mark.asyncio
async def test_list_template_categories_usecase_success():
    from src.modules.email_template.application.usecases.gallery.list_template_categories_usecase import (
        ListTemplateCategoriesUseCase,
    )

    category_one = _make_category()

    category_two = _make_category(
        id=2,
        uuid="category-uuid-2",
        name="Follow-up",
        display_order=2,
    )

    mock_category_service = AsyncMock()
    mock_category_service.list_active_categories = AsyncMock(
        return_value=[
            category_one,
            category_two,
        ]
    )

    usecase = ListTemplateCategoriesUseCase(
        template_category_domain_service=mock_category_service,
    )

    result = await usecase.execute()

    assert result == [
        category_one,
        category_two,
    ]

    mock_category_service.list_active_categories.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_list_template_categories_usecase_returns_empty_list():
    from src.modules.email_template.application.usecases.gallery.list_template_categories_usecase import (
        ListTemplateCategoriesUseCase,
    )

    mock_category_service = AsyncMock()
    mock_category_service.list_active_categories = AsyncMock(
        return_value=[]
    )

    usecase = ListTemplateCategoriesUseCase(
        template_category_domain_service=mock_category_service,
    )

    result = await usecase.execute()

    assert result == []

    mock_category_service.list_active_categories.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_list_template_categories_usecase_wraps_unexpected_error():
    from src.modules.email_template.application.usecases.gallery.list_template_categories_usecase import (
        ListTemplateCategoriesUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_category_service = AsyncMock()
    mock_category_service.list_active_categories = AsyncMock(
        side_effect=RuntimeError(
            "Unexpected category error",
        )
    )

    usecase = ListTemplateCategoriesUseCase(
        template_category_domain_service=mock_category_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute()

    mock_category_service.list_active_categories.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_list_template_categories_usecase_preserves_domain_error():
    from src.modules.email_template.application.usecases.gallery.list_template_categories_usecase import (
        ListTemplateCategoriesUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    mock_category_service = AsyncMock()
    mock_category_service.list_active_categories = AsyncMock(
        side_effect=InvalidError(
            error="Invalid template category",
        )
    )

    usecase = ListTemplateCategoriesUseCase(
        template_category_domain_service=mock_category_service,
    )

    with pytest.raises(InvalidError):
        await usecase.execute()

    mock_category_service.list_active_categories.assert_awaited_once_with()


## ---------------------------- List System Templates ---------------------------- ##


@pytest.mark.asyncio
async def test_list_system_templates_usecase_success():
    from src.modules.email_template.application.usecases.gallery.list_system_templates_usecase import (
        ListSystemTemplatesUseCase,
    )

    template_one = _make_template(
        id=1,
        uuid="system-template-uuid-1",
    )

    template_two = _make_template(
        id=2,
        uuid="system-template-uuid-2",
        name="System Follow-up Template",
    )

    mock_template_service = AsyncMock()
    mock_template_service.list_system_paginated = AsyncMock(
        return_value=(
            [
                template_one,
                template_two,
            ],
            2,
        )
    )

    usecase = ListSystemTemplatesUseCase(
        template_domain_service=mock_template_service,
    )

    templates, total = await usecase.execute(
        category_id=2,
        search="welcome",
        limit=20,
        offset=0,
    )

    assert templates == [
        template_one,
        template_two,
    ]
    assert total == 2

    mock_template_service.list_system_paginated.assert_awaited_once_with(
        category_id=2,
        search="welcome",
        limit=20,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_system_templates_usecase_uses_default_filters():
    from src.modules.email_template.application.usecases.gallery.list_system_templates_usecase import (
        ListSystemTemplatesUseCase,
    )

    mock_template_service = AsyncMock()
    mock_template_service.list_system_paginated = AsyncMock(
        return_value=([], 0)
    )

    usecase = ListSystemTemplatesUseCase(
        template_domain_service=mock_template_service,
    )

    templates, total = await usecase.execute()

    assert templates == []
    assert total == 0

    mock_template_service.list_system_paginated.assert_awaited_once_with(
        category_id=None,
        search=None,
        limit=20,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_system_templates_usecase_returns_empty_result():
    from src.modules.email_template.application.usecases.gallery.list_system_templates_usecase import (
        ListSystemTemplatesUseCase,
    )

    mock_template_service = AsyncMock()
    mock_template_service.list_system_paginated = AsyncMock(
        return_value=([], 0)
    )

    usecase = ListSystemTemplatesUseCase(
        template_domain_service=mock_template_service,
    )

    templates, total = await usecase.execute(
        category_id=10,
        search="missing",
        limit=50,
        offset=20,
    )

    assert templates == []
    assert total == 0

    mock_template_service.list_system_paginated.assert_awaited_once_with(
        category_id=10,
        search="missing",
        limit=50,
        offset=20,
    )


@pytest.mark.asyncio
async def test_list_system_templates_usecase_preserves_domain_error():
    from src.modules.email_template.application.usecases.gallery.list_system_templates_usecase import (
        ListSystemTemplatesUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    mock_template_service = AsyncMock()
    mock_template_service.list_system_paginated = AsyncMock(
        side_effect=InvalidError(
            error="Invalid category filter",
        )
    )

    usecase = ListSystemTemplatesUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(InvalidError):
        await usecase.execute(
            category_id=999,
        )


@pytest.mark.asyncio
async def test_list_system_templates_usecase_wraps_unexpected_error():
    from src.modules.email_template.application.usecases.gallery.list_system_templates_usecase import (
        ListSystemTemplatesUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.list_system_paginated = AsyncMock(
        side_effect=RuntimeError(
            "Unexpected template error",
        )
    )

    usecase = ListSystemTemplatesUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute()


## --------------------------- System Template Details --------------------------- ##


@pytest.mark.asyncio
async def test_get_system_template_details_usecase_success():
    from src.modules.email_template.application.usecases.gallery.get_system_template_details_usecase import (
        GetSystemTemplateDetailsUseCase,
    )

    template = _make_template()

    mock_template_service = AsyncMock()
    mock_template_service.get_system_template_by_uuid = AsyncMock(
        return_value=template
    )

    usecase = GetSystemTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
    )

    result = await usecase.execute(
        template_uuid="template-uuid",
    )

    assert result == template

    mock_template_service.get_system_template_by_uuid.assert_awaited_once_with(
        "template-uuid"
    )


@pytest.mark.asyncio
async def test_get_system_template_details_usecase_raises_when_not_found():
    from src.modules.email_template.application.usecases.gallery.get_system_template_details_usecase import (
        GetSystemTemplateDetailsUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_system_template_by_uuid = AsyncMock(
        return_value=None
    )

    usecase = GetSystemTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="missing-template-uuid",
        )

    mock_template_service.get_system_template_by_uuid.assert_awaited_once_with(
        "missing-template-uuid"
    )


@pytest.mark.asyncio
async def test_get_system_template_details_usecase_raises_when_id_is_missing():
    from src.modules.email_template.application.usecases.gallery.get_system_template_details_usecase import (
        GetSystemTemplateDetailsUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    template = _make_template(
        id=None,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_system_template_by_uuid = AsyncMock(
        return_value=template
    )

    usecase = GetSystemTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="template-uuid",
        )

    mock_template_service.get_system_template_by_uuid.assert_awaited_once_with(
        "template-uuid"
    )


@pytest.mark.asyncio
async def test_get_system_template_details_usecase_preserves_domain_error():
    from src.modules.email_template.application.usecases.gallery.get_system_template_details_usecase import (
        GetSystemTemplateDetailsUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    mock_template_service = AsyncMock()
    mock_template_service.get_system_template_by_uuid = AsyncMock(
        side_effect=InvalidError(
            error="System template is unavailable",
        )
    )

    usecase = GetSystemTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(InvalidError):
        await usecase.execute(
            template_uuid="template-uuid",
        )


## ---------------------------- Copy System Template ---------------------------- ##


@pytest.mark.asyncio
async def test_copy_system_template_usecase_success():
    from src.modules.email_template.application.usecases.gallery.copy_system_template_usecase import (
        CopySystemTemplateUseCase,
    )
    from src.modules.email_template.domain.events.template_domain_events import (
        TemplateCreatedEvent,
    )

    source_template = _make_template(
        id=5,
        uuid="system-template-uuid",
    )

    created_template = _make_template(
        id=6,
        uuid="copied-template-uuid",
        organization_id=10,
        source_template_id=5,
        name="System Welcome Template Copy",
        template_type="custom",
        status="draft",
        created_by_id=20,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_system_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.create_custom_template = AsyncMock(
        return_value=created_template
    )

    usecase = CopySystemTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.gallery."
        "copy_system_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            template_uuid="system-template-uuid",
            organization_id=10,
            actor_id=20,
        )

    assert result == created_template

    mock_template_service.get_system_template_by_uuid.assert_awaited_once_with(
        "system-template-uuid"
    )

    mock_template_service.create_custom_template.assert_awaited_once()

    copied_entity = (
        mock_template_service.create_custom_template.await_args.args[0]
    )

    assert copied_entity.organization_id == 10
    assert copied_entity.category_id == source_template.category_id
    assert copied_entity.source_template_id == 5
    assert copied_entity.name == "System Welcome Template Copy"
    assert copied_entity.description == source_template.description
    assert copied_entity.subject == source_template.subject
    assert copied_entity.body_html == source_template.body_html
    assert copied_entity.created_by_id == 20

    # These values are initialized by TemplateEntity defaults.
    assert copied_entity.template_type == "custom"
    assert copied_entity.status == "draft"

    # System-template content must remain unchanged in the copied draft.
    assert "{{first_name}}" in copied_entity.subject
    assert "{{first_name}}" in copied_entity.body_html
    assert "https://example.com" in copied_entity.body_html
    assert (
        "https://cdn.example.com/welcome.png"
        in copied_entity.body_html
    )
    assert "<button>Get Started</button>" in copied_entity.body_html

    mock_publish.assert_awaited_once()

    publish_call = mock_publish.await_args
    assert publish_call is not None

    event = publish_call.args[0]

    assert isinstance(
        event,
        TemplateCreatedEvent,
    )
    assert event.template_id == 6
    assert event.template_uuid == "copied-template-uuid"
    assert event.organization_id == 10
    assert event.created_by_id == 20


@pytest.mark.asyncio
async def test_copy_system_template_does_not_change_source_template():
    from src.modules.email_template.application.usecases.gallery.copy_system_template_usecase import (
        CopySystemTemplateUseCase,
    )

    source_template = _make_template(
        id=5,
        uuid="system-template-uuid",
    )

    original_source_values = {
        "organization_id": source_template.organization_id,
        "source_template_id": source_template.source_template_id,
        "name": source_template.name,
        "description": source_template.description,
        "subject": source_template.subject,
        "body_html": source_template.body_html,
        "template_type": source_template.template_type,
        "status": source_template.status,
    }

    created_template = _make_template(
        id=6,
        uuid="copied-template-uuid",
        organization_id=10,
        source_template_id=5,
        template_type="custom",
        status="draft",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_system_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.create_custom_template = AsyncMock(
        return_value=created_template
    )

    usecase = CopySystemTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.gallery."
        "copy_system_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ):
        await usecase.execute(
            template_uuid="system-template-uuid",
            organization_id=10,
            actor_id=20,
        )

    assert source_template.organization_id == (
        original_source_values["organization_id"]
    )
    assert source_template.source_template_id == (
        original_source_values["source_template_id"]
    )
    assert source_template.name == original_source_values["name"]
    assert (
        source_template.description
        == original_source_values["description"]
    )
    assert source_template.subject == original_source_values["subject"]
    assert (
        source_template.body_html
        == original_source_values["body_html"]
    )
    assert (
        source_template.template_type
        == original_source_values["template_type"]
    )
    assert source_template.status == original_source_values["status"]


@pytest.mark.asyncio
async def test_copy_system_template_usecase_raises_when_source_not_found():
    from src.modules.email_template.application.usecases.gallery.copy_system_template_usecase import (
        CopySystemTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    mock_template_service = AsyncMock()
    mock_template_service.get_system_template_by_uuid = AsyncMock(
        return_value=None
    )
    mock_template_service.create_custom_template = AsyncMock()

    usecase = CopySystemTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.gallery."
        "copy_system_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(CreateError):
            await usecase.execute(
                template_uuid="missing-template-uuid",
                organization_id=10,
                actor_id=20,
            )

    mock_template_service.get_system_template_by_uuid.assert_awaited_once_with(
        "missing-template-uuid"
    )
    mock_template_service.create_custom_template.assert_not_awaited()
    mock_publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_copy_system_template_usecase_raises_when_source_id_is_missing():
    from src.modules.email_template.application.usecases.gallery.copy_system_template_usecase import (
        CopySystemTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    source_template = _make_template(
        id=None,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_system_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.create_custom_template = AsyncMock()

    usecase = CopySystemTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(CreateError):
        await usecase.execute(
            template_uuid="system-template-uuid",
            organization_id=10,
            actor_id=20,
        )

    mock_template_service.create_custom_template.assert_not_awaited()


@pytest.mark.asyncio
async def test_copy_system_template_usecase_raises_when_created_id_is_missing():
    from src.modules.email_template.application.usecases.gallery.copy_system_template_usecase import (
        CopySystemTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    source_template = _make_template(
        id=5,
    )

    created_template = _make_template(
        id=None,
        organization_id=10,
        source_template_id=5,
        template_type="custom",
        status="draft",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_system_template_by_uuid = AsyncMock(
        return_value=source_template
    )
    mock_template_service.create_custom_template = AsyncMock(
        return_value=created_template
    )

    usecase = CopySystemTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.gallery."
        "copy_system_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(CreateError):
            await usecase.execute(
                template_uuid="system-template-uuid",
                organization_id=10,
                actor_id=20,
            )

    mock_template_service.create_custom_template.assert_awaited_once()
    mock_publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_copy_system_template_usecase_preserves_domain_error():
    from src.modules.email_template.application.usecases.gallery.copy_system_template_usecase import (
        CopySystemTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    mock_template_service = AsyncMock()
    mock_template_service.get_system_template_by_uuid = AsyncMock(
        side_effect=InvalidError(
            error="System template is unavailable",
        )
    )

    usecase = CopySystemTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(InvalidError):
        await usecase.execute(
            template_uuid="system-template-uuid",
            organization_id=10,
            actor_id=20,
        )

    mock_template_service.get_system_template_by_uuid.assert_awaited_once_with(
        "system-template-uuid"
    )