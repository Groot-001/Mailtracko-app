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
        "organization_id": 10,
        "category_id": 2,
        "source_template_id": None,
        "name": "Welcome Template",
        "description": "Welcome email",
        "subject": "Welcome {{first_name}}",
        "body_html": "<p>Hello {{first_name}}</p>",
        "template_type": "custom",
        "status": "draft",
        "is_active": True,
        "created_by_id": 20,
        "updated_by_id": None,
    }
    data.update(overrides)

    return TemplateEntity(**data)


def _make_asset(**overrides):
    from src.modules.email_template.domain.entities.template_asset_entity import (
        TemplateAssetEntity,
    )

    data = {
        "id": 1,
        "uuid": "asset-uuid",
        "template_id": 1,
        "organization_id": 10,
        "original_filename": "logo.png",
        "storage_key": "email-templates/10/logo-key",
        "file_url": "https://cdn.example.com/logo.png",
        "content_type": "image/png",
        "file_size": 128,
        "asset_type": "image",
        "usage": "inline",
        "is_active": True,
        "uploaded_by_id": 20,
    }
    data.update(overrides)

    return TemplateAssetEntity(**data)


def _make_asset_payload(usage: str = "inline"):
    from src.modules.email_template.domain.enums.template_enums import (
        TemplateAssetUsageEnum,
    )
    from src.modules.email_template.presentation.schemas.template_schemas import (
        CreateTemplateAssetRequestSchema,
    )

    return CreateTemplateAssetRequestSchema(
        usage=TemplateAssetUsageEnum(usage),
    )


@pytest.mark.asyncio
async def test_create_template_asset_usecase_uploads_inline_image():
    from src.modules.email_template.application.usecases.assets.create_template_asset_usecase import (
        CreateTemplateAssetUseCase,
    )
    from src.modules.email_template.domain.events.template_domain_events import (
        TemplateAssetCreatedEvent,
    )

    template = _make_template()
    created_asset = _make_asset()

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )

    mock_asset_service = AsyncMock()
    mock_asset_service.create_template_asset = AsyncMock(
        return_value=created_asset
    )

    mock_uploader = AsyncMock()
    mock_uploader.upload_files = AsyncMock(
        return_value=[
            {
                "storage_key": "email-templates/10/logo-key",
                "url": "https://cdn.example.com/logo.png",
                "original_filename": "logo.png",
                "content_type": "image/png",
                "size": 128,
            }
        ]
    )
    mock_uploader.delete_file = AsyncMock()

    usecase = CreateTemplateAssetUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
        uploader=mock_uploader,
    )

    with patch(
        "src.modules.email_template.application.usecases.assets."
        "create_template_asset_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_asset_payload("inline"),
            filename=" logo.png ",
            content=b"image-content",
            content_type="image/png",
            organization_id=10,
            actor_id=20,
        )

    assert result == created_asset

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="template-uuid",
        organization_id=10,
    )

    mock_uploader.upload_files.assert_awaited_once_with(
        [
            (
                "logo.png",
                b"image-content",
                "image/png",
            )
        ]
    )

    mock_asset_service.create_template_asset.assert_awaited_once()

    asset_entity = (
        mock_asset_service
        .create_template_asset
        .await_args
        .args[0]
    )

    assert asset_entity.template_id == 1
    assert asset_entity.organization_id == 10
    assert asset_entity.original_filename == "logo.png"
    assert asset_entity.storage_key == (
        "email-templates/10/logo-key"
    )
    assert asset_entity.file_url == (
        "https://cdn.example.com/logo.png"
    )
    assert asset_entity.content_type == "image/png"
    assert asset_entity.file_size == 128
    assert asset_entity.asset_type == "image"
    assert asset_entity.usage == "inline"
    assert asset_entity.is_active is True
    assert asset_entity.uploaded_by_id == 20

    mock_uploader.delete_file.assert_not_awaited()
    mock_publish.assert_awaited_once()

    mock_publish.assert_awaited_once()

    publish_call = mock_publish.await_args
    assert publish_call is not None

    event = publish_call.args[0]

    assert isinstance(
        event,
        TemplateAssetCreatedEvent,
    )
    assert event.asset_id == 1
    assert event.asset_uuid == "asset-uuid"
    assert event.template_id == 1
    assert event.organization_id == 10
    assert event.uploaded_by_id == 20


@pytest.mark.asyncio
async def test_create_template_asset_usecase_uploads_attachment():
    from src.modules.email_template.application.usecases.assets.create_template_asset_usecase import (
        CreateTemplateAssetUseCase,
    )

    template = _make_template()

    created_asset = _make_asset(
        original_filename="proposal.pdf",
        storage_key="email-templates/10/proposal-key",
        file_url="https://cdn.example.com/proposal.pdf",
        content_type="application/pdf",
        file_size=256,
        asset_type="document",
        usage="attachment",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )

    mock_asset_service = AsyncMock()
    mock_asset_service.create_template_asset = AsyncMock(
        return_value=created_asset
    )

    mock_uploader = AsyncMock()
    mock_uploader.upload_files = AsyncMock(
        return_value=[
            {
                "storage_key": "email-templates/10/proposal-key",
                "url": "https://cdn.example.com/proposal.pdf",
                "original_filename": "proposal.pdf",
                "content_type": "application/pdf",
                "size": 256,
            }
        ]
    )
    mock_uploader.delete_file = AsyncMock()

    usecase = CreateTemplateAssetUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
        uploader=mock_uploader,
    )

    with patch(
        "src.modules.email_template.application.usecases.assets."
        "create_template_asset_usecase.mediator.publish",
        new_callable=AsyncMock,
    ):
        result = await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_asset_payload("attachment"),
            filename="proposal.pdf",
            content=b"pdf-content",
            content_type="application/pdf",
            organization_id=10,
            actor_id=20,
        )

    assert result == created_asset

    asset_entity = (
        mock_asset_service
        .create_template_asset
        .await_args
        .args[0]
    )

    assert asset_entity.asset_type == "document"
    assert asset_entity.usage == "attachment"
    assert asset_entity.content_type == "application/pdf"


@pytest.mark.asyncio
async def test_create_template_asset_usecase_rejects_document_as_inline():
    from src.modules.email_template.application.usecases.assets.create_template_asset_usecase import (
        CreateTemplateAssetUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=_make_template()
    )

    mock_asset_service = AsyncMock()
    mock_uploader = AsyncMock()

    usecase = CreateTemplateAssetUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
        uploader=mock_uploader,
    )

    with pytest.raises(InvalidError):
        await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_asset_payload("inline"),
            filename="proposal.pdf",
            content=b"pdf-content",
            content_type="application/pdf",
            organization_id=10,
            actor_id=20,
        )

    mock_uploader.upload_files.assert_not_awaited()
    mock_asset_service.create_template_asset.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_template_asset_usecase_rejects_empty_file():
    from src.modules.email_template.application.usecases.assets.create_template_asset_usecase import (
        CreateTemplateAssetUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=_make_template()
    )

    mock_asset_service = AsyncMock()
    mock_uploader = AsyncMock()

    usecase = CreateTemplateAssetUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
        uploader=mock_uploader,
    )

    with pytest.raises(InvalidError):
        await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_asset_payload("inline"),
            filename="logo.png",
            content=b"",
            content_type="image/png",
            organization_id=10,
            actor_id=20,
        )

    mock_uploader.upload_files.assert_not_awaited()
    mock_asset_service.create_template_asset.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_template_asset_usecase_raises_when_template_missing():
    from src.modules.email_template.application.usecases.assets.create_template_asset_usecase import (
        CreateTemplateAssetUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=None
    )

    mock_asset_service = AsyncMock()
    mock_uploader = AsyncMock()

    usecase = CreateTemplateAssetUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
        uploader=mock_uploader,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="missing-template-uuid",
            payload=_make_asset_payload("inline"),
            filename="logo.png",
            content=b"image-content",
            content_type="image/png",
            organization_id=10,
            actor_id=20,
        )

    mock_uploader.upload_files.assert_not_awaited()
    mock_asset_service.create_template_asset.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_template_asset_usecase_deletes_upload_when_db_creation_fails():
    from src.modules.email_template.application.usecases.assets.create_template_asset_usecase import (
        CreateTemplateAssetUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=_make_template()
    )

    mock_asset_service = AsyncMock()
    mock_asset_service.create_template_asset = AsyncMock(
        side_effect=CreateError(
            error="Failed to save asset",
        )
    )

    mock_uploader = AsyncMock()
    mock_uploader.upload_files = AsyncMock(
        return_value=[
            {
                "storage_key": "email-templates/10/logo-key",
                "url": "https://cdn.example.com/logo.png",
                "original_filename": "logo.png",
                "content_type": "image/png",
                "size": 128,
            }
        ]
    )
    mock_uploader.delete_file = AsyncMock()

    usecase = CreateTemplateAssetUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
        uploader=mock_uploader,
    )

    with pytest.raises(CreateError):
        await usecase.execute(
            template_uuid="template-uuid",
            payload=_make_asset_payload("inline"),
            filename="logo.png",
            content=b"image-content",
            content_type="image/png",
            organization_id=10,
            actor_id=20,
        )

    mock_uploader.delete_file.assert_awaited_once_with(
        "email-templates/10/logo-key"
    )


@pytest.mark.asyncio
async def test_list_template_assets_usecase_success():
    from src.modules.email_template.application.usecases.assets.list_template_assets_usecase import (
        ListTemplateAssetsUseCase,
    )

    asset_one = _make_asset()

    asset_two = _make_asset(
        id=2,
        uuid="asset-uuid-2",
        original_filename="proposal.pdf",
        storage_key="email-templates/10/proposal-key",
        file_url="https://cdn.example.com/proposal.pdf",
        content_type="application/pdf",
        file_size=256,
        asset_type="document",
        usage="attachment",
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=_make_template()
    )

    mock_asset_service = AsyncMock()
    mock_asset_service.list_paginated = AsyncMock(
        return_value=(
            [
                asset_one,
                asset_two,
            ],
            2,
        )
    )

    usecase = ListTemplateAssetsUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
    )

    assets, total = await usecase.execute(
        template_uuid="template-uuid",
        organization_id=10,
        usage="attachment",
        asset_type="document",
        limit=50,
        offset=0,
    )

    assert assets == [
        asset_one,
        asset_two,
    ]
    assert total == 2

    mock_template_service.get_custom_template_by_uuid.assert_awaited_once_with(
        template_uuid="template-uuid",
        organization_id=10,
    )

    mock_asset_service.list_paginated.assert_awaited_once_with(
        template_id=1,
        organization_id=10,
        usage="attachment",
        asset_type="document",
        limit=50,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_template_assets_usecase_raises_when_template_missing():
    from src.modules.email_template.application.usecases.assets.list_template_assets_usecase import (
        ListTemplateAssetsUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=None
    )

    mock_asset_service = AsyncMock()

    usecase = ListTemplateAssetsUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="missing-template-uuid",
            organization_id=10,
        )

    mock_asset_service.list_paginated.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_template_asset_usecase_success():
    from src.modules.email_template.application.usecases.assets.delete_template_asset_usecase import (
        DeleteTemplateAssetUseCase,
    )
    from src.modules.email_template.domain.events.template_domain_events import (
        TemplateAssetDeletedEvent,
    )

    template = _make_template()
    asset = _make_asset()

    deleted_asset = _make_asset(
        is_active=False,
    )

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=template
    )

    mock_asset_service = AsyncMock()
    mock_asset_service.get_template_asset_by_uuid = AsyncMock(
        return_value=asset
    )
    mock_asset_service.delete_template_asset = AsyncMock(
        return_value=deleted_asset
    )

    mock_uploader = AsyncMock()
    mock_uploader.delete_file = AsyncMock()

    usecase = DeleteTemplateAssetUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
        uploader=mock_uploader,
    )

    with patch(
        "src.modules.email_template.application.usecases.assets."
        "delete_template_asset_usecase.mediator.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        result = await usecase.execute(
            template_uuid="template-uuid",
            asset_uuid="asset-uuid",
            organization_id=10,
            actor_id=20,
        )

    assert result == deleted_asset

    mock_asset_service.get_template_asset_by_uuid.assert_awaited_once_with(
        asset_uuid="asset-uuid",
        template_id=1,
        organization_id=10,
    )

    mock_asset_service.delete_template_asset.assert_awaited_once_with(
        asset_uuid="asset-uuid",
        template_id=1,
        organization_id=10,
    )

    mock_uploader.delete_file.assert_awaited_once_with(
        "email-templates/10/logo-key"
    )

    mock_publish.assert_awaited_once()

    mock_publish.assert_awaited_once()

    publish_call = mock_publish.await_args
    assert publish_call is not None

    event = publish_call.args[0]

    assert isinstance(
        event,
        TemplateAssetDeletedEvent,
    )
    assert event.asset_id == 1
    assert event.asset_uuid == "asset-uuid"
    assert event.template_id == 1
    assert event.organization_id == 10
    assert event.deleted_by_id == 20


@pytest.mark.asyncio
async def test_delete_template_asset_usecase_raises_when_asset_missing():
    from src.modules.email_template.application.usecases.assets.delete_template_asset_usecase import (
        DeleteTemplateAssetUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=_make_template()
    )

    mock_asset_service = AsyncMock()
    mock_asset_service.get_template_asset_by_uuid = AsyncMock(
        return_value=None
    )

    mock_uploader = AsyncMock()

    usecase = DeleteTemplateAssetUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
        uploader=mock_uploader,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="template-uuid",
            asset_uuid="missing-asset-uuid",
            organization_id=10,
            actor_id=20,
        )

    mock_asset_service.delete_template_asset.assert_not_awaited()
    mock_uploader.delete_file.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_template_asset_usecase_wraps_uploader_error():
    from src.modules.email_template.application.usecases.assets.delete_template_asset_usecase import (
        DeleteTemplateAssetUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_template_service = AsyncMock()
    mock_template_service.get_custom_template_by_uuid = AsyncMock(
        return_value=_make_template()
    )

    mock_asset_service = AsyncMock()
    mock_asset_service.get_template_asset_by_uuid = AsyncMock(
        return_value=_make_asset()
    )
    mock_asset_service.delete_template_asset = AsyncMock(
        return_value=_make_asset(
            is_active=False,
        )
    )

    mock_uploader = AsyncMock()
    mock_uploader.delete_file = AsyncMock(
        side_effect=RuntimeError(
            "Cloudinary delete failed",
        )
    )

    usecase = DeleteTemplateAssetUseCase(
        template_domain_service=mock_template_service,
        template_asset_domain_service=mock_asset_service,
        uploader=mock_uploader,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            template_uuid="template-uuid",
            asset_uuid="asset-uuid",
            organization_id=10,
            actor_id=20,
        )