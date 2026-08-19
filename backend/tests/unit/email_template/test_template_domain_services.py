from unittest.mock import AsyncMock

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


def _make_category(**overrides):
    from src.modules.email_template.domain.entities.template_category_entity import (
        TemplateCategoryEntity,
    )

    data = {
        "id": 1,
        "uuid": "category-uuid",
        "name": "Welcome",
        "description": "Welcome templates",
        "display_order": 1,
        "is_active": True,
        "created_by_id": 20,
        "updated_by_id": None,
    }
    data.update(overrides)

    return TemplateCategoryEntity(**data)


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


## -------------------- Template domain service -------------------- ##


@pytest.mark.asyncio
async def test_template_domain_service_creates_custom_template_as_draft():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )

    template = _make_template(
        template_type="system",
        status="published",
        is_active=False,
    )

    repository = AsyncMock()
    repository.add = AsyncMock(
        return_value=template
    )

    service = TemplateDomainService(
        repository=repository,
    )

    result = await service.create_custom_template(
        template,
    )

    assert result == template
    assert template.template_type == "custom"
    assert template.status == "draft"
    assert template.is_active is True
    assert template.published_at is None
    assert template.archived_at is None

    repository.add.assert_awaited_once_with(
        template,
    )


@pytest.mark.asyncio
async def test_template_domain_service_rejects_missing_organization():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    repository = AsyncMock()

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.create_custom_template(
            _make_template(
                organization_id=None,
            )
        )

    repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_rejects_blank_name():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    repository = AsyncMock()

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.create_custom_template(
            _make_template(
                name="   ",
            )
        )

    repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_updates_custom_template():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )

    template = _make_template()

    repository = AsyncMock()
    repository.update = AsyncMock(
        return_value=template
    )

    service = TemplateDomainService(
        repository=repository,
    )

    result = await service.update_custom_template(
        template_entity=template,
        actor_id=30,
    )

    assert result == template
    assert template.updated_by_id == 30

    repository.update.assert_awaited_once_with(
        template,
    )


@pytest.mark.asyncio
async def test_template_domain_service_rejects_updating_non_draft_template():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    template = _make_template(
        status="published",
    )

    repository = AsyncMock()
    repository.update = AsyncMock(
        return_value=template
    )

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.update_custom_template(
            template_entity=template,
            actor_id=30,
        )

    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_prevents_system_template_update():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    repository = AsyncMock()

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.update_custom_template(
            template_entity=_make_template(
                template_type="system",
            ),
            actor_id=30,
        )

    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_publishes_custom_template():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )

    template = _make_template(
        status="draft",
    )

    repository = AsyncMock()
    repository.get_by = AsyncMock(
        return_value=template
    )
    repository.update = AsyncMock(
        return_value=template
    )

    service = TemplateDomainService(
        repository=repository,
    )

    result = await service.publish_custom_template(
        template_id=1,
        organization_id=10,
        actor_id=30,
    )

    assert result == template
    assert template.status == "published"
    assert template.published_at is not None
    assert template.archived_at is None
    assert template.updated_by_id == 30

    repository.get_by.assert_awaited_once_with(
        id=1,
        organization_id=10,
        deleted_at=None,
    )

    repository.update.assert_awaited_once_with(
        template,
    )


@pytest.mark.asyncio
async def test_template_domain_service_rejects_publish_without_subject():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    template = _make_template(
        subject="   ",
    )

    repository = AsyncMock()
    repository.get_by = AsyncMock(
        return_value=template
    )

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.publish_custom_template(
            template_id=1,
            organization_id=10,
            actor_id=30,
        )

    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_rejects_already_published_template():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    repository = AsyncMock()
    repository.get_by = AsyncMock(
        return_value=_make_template(
            status="published",
        )
    )

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.publish_custom_template(
            template_id=1,
            organization_id=10,
            actor_id=30,
        )

    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_archives_published_template():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )

    template = _make_template(
        status="published",
    )

    repository = AsyncMock()
    repository.get_by = AsyncMock(
        return_value=template
    )
    repository.count_campaign_usages = AsyncMock(
        return_value=0
    )
    repository.update = AsyncMock(
        return_value=template
    )

    service = TemplateDomainService(
        repository=repository,
    )

    result = await service.archive_custom_template(
        template_id=1,
        organization_id=10,
        actor_id=30,
    )

    assert result == template
    assert template.status == "archived"
    assert template.archived_at is not None
    assert template.updated_by_id == 30

    repository.update.assert_awaited_once_with(
        template,
    )


@pytest.mark.asyncio
async def test_template_domain_service_rejects_archiving_template_used_by_campaigns():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    template = _make_template(
        status="published",
    )

    repository = AsyncMock()
    repository.get_by = AsyncMock(
        return_value=template
    )
    repository.count_campaign_usages = AsyncMock(
        return_value=2
    )

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.archive_custom_template(
            template_id=1,
            organization_id=10,
            actor_id=30,
        )

    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_rejects_archiving_draft():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    repository = AsyncMock()
    repository.get_by = AsyncMock(
        return_value=_make_template(
            status="draft",
        )
    )
    repository.count_campaign_usages = AsyncMock(
        return_value=0
    )

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.archive_custom_template(
            template_id=1,
            organization_id=10,
            actor_id=30,
        )

    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_soft_deletes_template():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )

    template = _make_template()

    repository = AsyncMock()
    repository.get_by = AsyncMock(
        return_value=template
    )
    repository.count_campaign_usages = AsyncMock(
        return_value=0
    )
    repository.update = AsyncMock(
        return_value=template
    )

    service = TemplateDomainService(
        repository=repository,
    )

    result = await service.delete_custom_template(
        template_id=1,
        organization_id=10,
        actor_id=30,
    )

    assert result == template
    assert template.is_active is False
    assert template.deleted_at is not None
    assert template.updated_by_id == 30

    repository.update.assert_awaited_once_with(
        template,
    )


@pytest.mark.asyncio
async def test_template_domain_service_rejects_deleting_template_used_by_campaigns():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    template = _make_template()

    repository = AsyncMock()
    repository.get_by = AsyncMock(
        return_value=template
    )
    repository.count_campaign_usages = AsyncMock(
        return_value=1
    )

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.delete_custom_template(
            template_id=1,
            organization_id=10,
            actor_id=30,
        )

    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_restores_archived_template_to_draft():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )

    template = _make_template(
        status="archived",
        published_at=None,
        archived_at=None,
    )
    template.archive()

    repository = AsyncMock()
    repository.get_by = AsyncMock(
        return_value=template
    )
    repository.update = AsyncMock(
        return_value=template
    )

    service = TemplateDomainService(
        repository=repository,
    )

    result = await service.restore_custom_template(
        template_id=1,
        organization_id=10,
        actor_id=30,
    )

    assert result == template
    assert template.status == "draft"
    assert template.archived_at is None
    assert template.published_at is None
    assert template.updated_by_id == 30

    repository.update.assert_awaited_once_with(
        template,
    )


@pytest.mark.asyncio
async def test_template_domain_service_rejects_restoring_non_archived_template():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    repository = AsyncMock()
    repository.get_by = AsyncMock(
        return_value=_make_template(status="published")
    )

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.restore_custom_template(
            template_id=1,
            organization_id=10,
            actor_id=30,
        )

    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_validates_list_status():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    repository = AsyncMock()

    service = TemplateDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.list_custom_paginated(
            organization_id=10,
            status="invalid-status",
        )

    repository.list_custom_paginated.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_domain_service_lists_custom_templates():
    from src.modules.email_template.domain.services.template_domain_service import (
        TemplateDomainService,
    )

    template = _make_template()

    repository = AsyncMock()
    repository.list_custom_paginated = AsyncMock(
        return_value=(
            [template],
            1,
        )
    )

    service = TemplateDomainService(
        repository=repository,
    )

    templates, total = await service.list_custom_paginated(
        organization_id=10,
        status="draft",
        category_id=2,
        search="welcome",
        limit=20,
        offset=0,
    )

    assert templates == [
        template,
    ]
    assert total == 1

    repository.list_custom_paginated.assert_awaited_once_with(
        organization_id=10,
        status="draft",
        category_id=2,
        search="welcome",
        limit=20,
        offset=0,
        include_archived=False,
    )


## -------------------- Category domain service -------------------- ##


@pytest.mark.asyncio
async def test_category_domain_service_creates_active_category():
    from src.modules.email_template.domain.services.template_category_domain_service import (
        TemplateCategoryDomainService,
    )

    category = _make_category(
        is_active=False,
    )

    repository = AsyncMock()
    repository.find_active_by_name = AsyncMock(return_value=None)
    repository.add = AsyncMock(
        return_value=category
    )

    service = TemplateCategoryDomainService(
        repository=repository,
    )

    result = await service.create_template_category(
        category,
    )

    assert result == category
    assert category.is_active is True

    repository.add.assert_awaited_once_with(
        category,
    )


@pytest.mark.asyncio
async def test_category_domain_service_rejects_negative_display_order():
    from src.modules.email_template.domain.services.template_category_domain_service import (
        TemplateCategoryDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    repository = AsyncMock()

    service = TemplateCategoryDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.create_template_category(
            _make_category(
                display_order=-1,
            )
        )

    repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_category_domain_service_lists_active_categories():
    from src.modules.email_template.domain.services.template_category_domain_service import (
        TemplateCategoryDomainService,
    )

    category = _make_category()

    repository = AsyncMock()
    repository.list_active = AsyncMock(
        return_value=[
            category,
        ]
    )

    service = TemplateCategoryDomainService(
        repository=repository,
    )

    result = await service.list_active_categories()

    assert result == [
        category,
    ]

    repository.list_active.assert_awaited_once_with()


## -------------------- Asset domain service -------------------- ##


@pytest.mark.asyncio
async def test_asset_domain_service_creates_valid_asset():
    from src.modules.email_template.domain.services.template_asset_domain_service import (
        TemplateAssetDomainService,
    )

    asset = _make_asset(
        is_active=False,
    )

    repository = AsyncMock()
    repository.add = AsyncMock(
        return_value=asset
    )

    service = TemplateAssetDomainService(
        repository=repository,
    )

    result = await service.create_template_asset(
        asset,
    )

    assert result == asset
    assert asset.is_active is True

    repository.add.assert_awaited_once_with(
        asset,
    )


@pytest.mark.asyncio
async def test_asset_domain_service_rejects_document_inline_usage():
    from src.modules.email_template.domain.services.template_asset_domain_service import (
        TemplateAssetDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    repository = AsyncMock()

    service = TemplateAssetDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.create_template_asset(
            _make_asset(
                asset_type="document",
                usage="inline",
                content_type="application/pdf",
            )
        )

    repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_asset_domain_service_rejects_zero_file_size():
    from src.modules.email_template.domain.services.template_asset_domain_service import (
        TemplateAssetDomainService,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    repository = AsyncMock()

    service = TemplateAssetDomainService(
        repository=repository,
    )

    with pytest.raises(InvalidError):
        await service.create_template_asset(
            _make_asset(
                file_size=0,
            )
        )

    repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_asset_domain_service_lists_paginated_assets():
    from src.modules.email_template.domain.services.template_asset_domain_service import (
        TemplateAssetDomainService,
    )

    asset = _make_asset()

    repository = AsyncMock()
    repository.list_paginated = AsyncMock(
        return_value=(
            [asset],
            1,
        )
    )

    service = TemplateAssetDomainService(
        repository=repository,
    )

    assets, total = await service.list_paginated(
        template_id=1,
        organization_id=10,
        usage="inline",
        asset_type="image",
        limit=50,
        offset=0,
    )

    assert assets == [
        asset,
    ]
    assert total == 1

    repository.list_paginated.assert_awaited_once_with(
        template_id=1,
        organization_id=10,
        usage="inline",
        asset_type="image",
        limit=50,
        offset=0,
    )


@pytest.mark.asyncio
async def test_asset_domain_service_soft_deletes_asset():
    from src.modules.email_template.domain.services.template_asset_domain_service import (
        TemplateAssetDomainService,
    )

    asset = _make_asset()

    repository = AsyncMock()
    repository.get_by_uuid_and_template_id = AsyncMock(
        return_value=asset
    )
    repository.update = AsyncMock(
        return_value=asset
    )

    service = TemplateAssetDomainService(
        repository=repository,
    )

    result = await service.delete_template_asset(
        asset_uuid="asset-uuid",
        template_id=1,
        organization_id=10,
    )

    assert result == asset
    assert asset.is_active is False
    assert asset.deleted_at is not None

    repository.get_by_uuid_and_template_id.assert_awaited_once_with(
        asset_uuid="asset-uuid",
        template_id=1,
        organization_id=10,
    )

    repository.update.assert_awaited_once_with(
        asset,
    )
