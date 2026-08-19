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


def _make_create_payload(**overrides):
    from src.modules.email_template.presentation.schemas.template_schemas import (
        CreateTemplateRequestSchema,
    )

    data = {
        "name": "Welcome Template",
        "description": "Welcome email for new contacts",
        "subject": "Welcome {{first_name}}",
        "body_html": "<p>Hello {{first_name}}</p>",
        "category_id": 2,
    }

    data.update(overrides)

    return CreateTemplateRequestSchema(**data)



def _make_category_service():
    service = AsyncMock()
    service.get_available_category_by_id = AsyncMock(return_value=object())
    return service

def _make_update_payload(**overrides):
    from src.modules.email_template.presentation.schemas.template_schemas import (
        UpdateTemplateRequestSchema,
    )

    return UpdateTemplateRequestSchema(**overrides)


@pytest.mark.asyncio
async def test_create_template_usecase_success():
    from src.modules.email_template.application.usecases.core.create_template_usecase import (
        CreateTemplateUseCase,
    )

    created_template = _make_template()

    mock_template_service = AsyncMock()
    mock_template_service.create_custom_template = AsyncMock(
        return_value=created_template
    )

    usecase = CreateTemplateUseCase(
        template_domain_service=mock_template_service,
        template_category_domain_service=_make_category_service(),
    )

    with patch(
        "src.modules.email_template.application.usecases.core."
        "create_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            payload=_make_create_payload(),
            organization_id=1,
            actor_id=10,
        )

    assert result["uuid"] == "template-uuid"
    assert result["organization_id"] == 1
    assert result["category_id"] == 2
    assert result["source_template_id"] is None
    assert result["name"] == "Welcome Template"
    assert result["description"] == "Welcome email for new contacts"
    assert result["subject"] == "Welcome {{first_name}}"
    assert result["body_html"] == "<p>Hello {{first_name}}</p>"
    assert result["template_type"] == "custom"
    assert result["status"] == "draft"
    assert result["is_active"] is True
    assert result["published_at"] is None
    assert result["archived_at"] is None

    mock_template_service.create_custom_template.assert_awaited_once()

    created_entity = (
        mock_template_service.create_custom_template.await_args.args[0]
    )

    assert created_entity.organization_id == 1
    assert created_entity.category_id == 2
    assert created_entity.name == "Welcome Template"
    assert created_entity.description == (
        "Welcome email for new contacts"
    )
    assert created_entity.subject == "Welcome {{first_name}}"
    assert created_entity.body_html == (
        "<p>Hello {{first_name}}</p>"
    )
    assert created_entity.template_type == "custom"
    assert created_entity.status == "draft"
    assert created_entity.created_by_id == 10

    mock_publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_template_usecase_raises_create_error_when_created_template_has_no_id():
    from src.modules.email_template.application.usecases.core.create_template_usecase import (
        CreateTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    created_template = _make_template(id=None)

    mock_template_service = AsyncMock()
    mock_template_service.create_custom_template = AsyncMock(
        return_value=created_template
    )

    usecase = CreateTemplateUseCase(
        template_domain_service=mock_template_service,
        template_category_domain_service=_make_category_service(),
    )

    with patch(
        "src.modules.email_template.application.usecases.core."
        "create_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(CreateError):
            await usecase.execute(
                payload=_make_create_payload(),
                organization_id=1,
                actor_id=10,
            )

    mock_template_service.create_custom_template.assert_awaited_once()
    mock_publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_template_usecase_preserves_domain_error():
    from src.modules.email_template.application.usecases.core.create_template_usecase import (
        CreateTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    mock_template_service = AsyncMock()
    mock_template_service.create_custom_template = AsyncMock(
        side_effect=InvalidError(
            error="Invalid custom template",
        )
    )

    usecase = CreateTemplateUseCase(
        template_domain_service=mock_template_service,
        template_category_domain_service=_make_category_service(),
    )

    with pytest.raises(InvalidError):
        await usecase.execute(
            payload=_make_create_payload(),
            organization_id=1,
            actor_id=10,
        )


@pytest.mark.asyncio
async def test_get_template_details_usecase_success():
    from src.modules.email_template.application.usecases.core.get_template_details_usecase import (
        GetTemplateDetailsUseCase,
    )

    template = _make_template()

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )

    usecase = GetTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
    )

    result = await usecase.execute(
        template_uuid="template-uuid",
        organization_id=1,
    )

    assert result == template

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="template-uuid",
        organization_id=1,
    )


@pytest.mark.asyncio
async def test_get_template_details_usecase_raises_server_error_when_template_not_found():
    from src.modules.email_template.application.usecases.core.get_template_details_usecase import (
        GetTemplateDetailsUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=None
    )

    usecase = GetTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="missing-template-uuid",
            organization_id=1,
        )

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="missing-template-uuid",
        organization_id=1,
    )


@pytest.mark.asyncio
async def test_get_template_details_usecase_raises_when_template_has_no_id():
    from src.modules.email_template.application.usecases.core.get_template_details_usecase import (
        GetTemplateDetailsUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    template = _make_template(id=None)

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )

    usecase = GetTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="template-uuid",
            organization_id=1,
        )


@pytest.mark.asyncio
async def test_list_templates_usecase_success():
    from src.modules.email_template.application.usecases.core.list_templates_usecase import (
        ListTemplatesUseCase,
    )

    template_one = _make_template(
        id=1,
        uuid="template-uuid-1",
        name="Welcome Template",
    )
    template_two = _make_template(
        id=2,
        uuid="template-uuid-2",
        name="Follow-up Template",
        subject="Following up",
        body_html="<p>Following up</p>",
        status="published",
    )

    mock_template_service = AsyncMock()
    mock_template_service.list_custom_paginated = AsyncMock(
        return_value=(
            [template_one, template_two],
            2,
        )
    )

    usecase = ListTemplatesUseCase(
        template_domain_service=mock_template_service,
    )

    templates, total = await usecase.execute(
        organization_id=1,
        status="published",
        include_archived=False,
        category_id=2,
        search="template",
        limit=20,
        offset=0,
    )

    assert templates == [template_one, template_two]
    assert total == 2

    mock_template_service.list_custom_paginated.assert_awaited_once_with(
        organization_id=1,
        status="published",
        include_archived=False,
        category_id=2,
        search="template",
        limit=20,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_templates_usecase_returns_empty_result():
    from src.modules.email_template.application.usecases.core.list_templates_usecase import (
        ListTemplatesUseCase,
    )

    mock_template_service = AsyncMock()
    mock_template_service.list_custom_paginated = AsyncMock(
        return_value=([], 0)
    )

    usecase = ListTemplatesUseCase(
        template_domain_service=mock_template_service,
    )

    templates, total = await usecase.execute(
        organization_id=1,
        status=None,
        include_archived=False,
        category_id=None,
        search=None,
        limit=20,
        offset=0,
    )

    assert templates == []
    assert total == 0

    mock_template_service.list_custom_paginated.assert_awaited_once_with(
        organization_id=1,
        status=None,
        include_archived=False,
        category_id=None,
        search=None,
        limit=20,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_templates_usecase_wraps_unexpected_error():
    from src.modules.email_template.application.usecases.core.list_templates_usecase import (
        ListTemplatesUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.list_custom_paginated = AsyncMock(
        side_effect=RuntimeError("Unexpected repository error")
    )

    usecase = ListTemplatesUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            organization_id=1,
            limit=20,
            offset=0,
        )


@pytest.mark.asyncio
async def test_edit_template_details_usecase_success():
    from src.modules.email_template.application.usecases.core.edit_template_details_usecase import (
        EditTemplateDetailsUseCase,
    )

    template = _make_template(
        name="Old Template",
        description="Old description",
        subject="Old subject",
        body_html="<p>Old body</p>",
        category_id=1,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )
    mock_template_service.update_custom_template = AsyncMock(
        return_value=template
    )

    usecase = EditTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
        template_category_domain_service=_make_category_service(),
    )

    with patch(
        "src.modules.email_template.application.usecases.core."
        "edit_template_details_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_update_payload(
                name="Updated Template",
                description="Updated description",
                subject="Updated subject",
                body_html="<p>Updated body</p>",
                category_id=3,
            ),
            organization_id=1,
            actor_id=10,
        )

    assert result == template
    assert template.name == "Updated Template"
    assert template.description == "Updated description"
    assert template.subject == "Updated subject"
    assert template.body_html == "<p>Updated body</p>"
    assert template.category_id == 3

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="template-uuid",
        organization_id=1,
    )
    mock_template_service.update_custom_template.assert_awaited_once_with(
        template,
        10,
    )
    mock_publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_edit_template_details_usecase_can_clear_optional_fields():
    from src.modules.email_template.application.usecases.core.edit_template_details_usecase import (
        EditTemplateDetailsUseCase,
    )

    template = _make_template(
        description="Existing description",
        category_id=2,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )
    mock_template_service.update_custom_template = AsyncMock(
        return_value=template
    )

    usecase = EditTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
        template_category_domain_service=_make_category_service(),
    )

    with patch(
        "src.modules.email_template.application.usecases.core."
        "edit_template_details_usecase.mediator.publish",
        new_callable=AsyncMock,
    ):
        result = await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_update_payload(
                description=None,
                category_id=None,
            ),
            organization_id=1,
            actor_id=10,
        )

    assert result == template
    assert template.description is None
    assert template.category_id is None

    mock_template_service.update_custom_template.assert_awaited_once_with(
        template,
        10,
    )


@pytest.mark.asyncio
async def test_edit_template_details_usecase_returns_same_template_when_no_fields():
    from src.modules.email_template.application.usecases.core.edit_template_details_usecase import (
        EditTemplateDetailsUseCase,
    )

    template = _make_template()

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )
    mock_template_service.update_custom_template = AsyncMock()

    usecase = EditTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
        template_category_domain_service=_make_category_service(),
    )

    with patch(
        "src.modules.email_template.application.usecases.core."
        "edit_template_details_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_update_payload(),
            organization_id=1,
            actor_id=10,
        )

    assert result == template

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="template-uuid",
        organization_id=1,
    )
    mock_template_service.update_custom_template.assert_not_awaited()

    # The current implementation still creates an update event even when
    # no editable fields were supplied.
    mock_publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_edit_template_details_usecase_raises_server_error_when_template_not_found():
    from src.modules.email_template.application.usecases.core.edit_template_details_usecase import (
        EditTemplateDetailsUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=None
    )
    mock_template_service.update_custom_template = AsyncMock()

    usecase = EditTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
        template_category_domain_service=_make_category_service(),
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="missing-template-uuid",
            payload=_make_update_payload(
                name="Updated Template",
            ),
            organization_id=1,
            actor_id=10,
        )

    mock_template_service.update_custom_template.assert_not_awaited()


@pytest.mark.asyncio
async def test_edit_template_details_usecase_raises_when_updated_template_has_no_id():
    from src.modules.email_template.application.usecases.core.edit_template_details_usecase import (
        EditTemplateDetailsUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    template = _make_template()
    updated_template = _make_template(
        id=None,
        name="Updated Template",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )
    mock_template_service.update_custom_template = AsyncMock(
        return_value=updated_template
    )

    usecase = EditTemplateDetailsUseCase(
        template_domain_service=mock_template_service,
        template_category_domain_service=_make_category_service(),
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_update_payload(
                name="Updated Template",
            ),
            organization_id=1,
            actor_id=10,
        )


@pytest.mark.asyncio
async def test_delete_template_usecase_success():
    from src.modules.email_template.application.usecases.core.delete_template_usecase import (
        DeleteTemplateUseCase,
    )

    template = _make_template()
    deleted_template = _make_template(
        is_active=False,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )
    mock_template_service.delete_custom_template = AsyncMock(
        return_value=deleted_template
    )

    usecase = DeleteTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.core."
        "delete_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            template_uuid="template-uuid",
            organization_id=1,
            actor_id=10,
        )

    assert result == deleted_template

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="template-uuid",
        organization_id=1,
    )
    mock_template_service.delete_custom_template.assert_awaited_once_with(
        template_id=1,
        organization_id=1,
        actor_id=10,
    )
    mock_publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_template_usecase_raises_server_error_when_template_not_found():
    from src.modules.email_template.application.usecases.core.delete_template_usecase import (
        DeleteTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=None
    )
    mock_template_service.delete_custom_template = AsyncMock()

    usecase = DeleteTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="missing-template-uuid",
            organization_id=1,
            actor_id=10,
        )

    mock_template_service.delete_custom_template.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_template_usecase_raises_when_deleted_template_has_no_id():
    from src.modules.email_template.application.usecases.core.delete_template_usecase import (
        DeleteTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    template = _make_template()
    deleted_template = _make_template(id=None)

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )
    mock_template_service.delete_custom_template = AsyncMock(
        return_value=deleted_template
    )

    usecase = DeleteTemplateUseCase(
        template_domain_service=mock_template_service,
    )

    with patch(
        "src.modules.email_template.application.usecases.core."
        "delete_template_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        with pytest.raises(ServerError):
            await usecase.execute(
                template_uuid="template-uuid",
                organization_id=1,
                actor_id=10,
            )

    mock_template_service.delete_custom_template.assert_awaited_once_with(
        template_id=1,
        organization_id=1,
        actor_id=10,
    )
    mock_publish.assert_not_awaited()
