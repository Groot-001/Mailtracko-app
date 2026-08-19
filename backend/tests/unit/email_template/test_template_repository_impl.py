from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.elements import TextClause

from src.modules.email_template.infrastructure.repositories.template_repository_impl import (
    TemplateRepositoryImpl,
)
from src.shared.exceptions.base_exceptions import ServerError


def _make_repository_with_scalar_result(total_usage: int):
    session = AsyncMock()
    result = Mock()
    result.scalar_one.return_value = total_usage
    session.execute = AsyncMock(return_value=result)
    repository = TemplateRepositoryImpl(session=session)
    return repository, session


def _assert_query_shape(statement) -> None:
    assert not isinstance(statement, TextClause)
    compiled_sql = str(statement)
    # Ensure direct campaign template references are counted.
    assert "campaigns.template_id" in compiled_sql
    # Ensure sequence-step template references are counted.
    assert "campaign_sequence_steps.template_id" in compiled_sql
    # Ensure A/B variant template references are counted.
    assert "campaign_ab_variants.template_id" in compiled_sql
    # Ensure organization and non-deleted campaign filtering remains enforced.
    assert "campaigns.organization_id" in compiled_sql
    assert "campaigns.deleted_at IS NULL" in compiled_sql


@pytest.mark.asyncio
async def test_count_campaign_usages_counts_direct_campaign_template_usage():
    repository, session = _make_repository_with_scalar_result(total_usage=1)

    total = await repository.count_campaign_usages(
        template_id=11,
        organization_id=7,
    )

    assert total == 1
    session.execute.assert_awaited_once()
    statement = session.execute.await_args.args[0]
    _assert_query_shape(statement)


@pytest.mark.asyncio
async def test_count_campaign_usages_counts_sequence_step_template_usage():
    repository, session = _make_repository_with_scalar_result(total_usage=1)

    total = await repository.count_campaign_usages(
        template_id=22,
        organization_id=7,
    )

    assert total == 1
    session.execute.assert_awaited_once()
    statement = session.execute.await_args.args[0]
    _assert_query_shape(statement)


@pytest.mark.asyncio
async def test_count_campaign_usages_counts_ab_variant_template_usage():
    repository, session = _make_repository_with_scalar_result(total_usage=1)

    total = await repository.count_campaign_usages(
        template_id=33,
        organization_id=7,
    )

    assert total == 1
    session.execute.assert_awaited_once()
    statement = session.execute.await_args.args[0]
    _assert_query_shape(statement)


@pytest.mark.asyncio
async def test_count_campaign_usages_returns_zero_when_template_is_unused():
    repository, session = _make_repository_with_scalar_result(total_usage=0)

    total = await repository.count_campaign_usages(
        template_id=44,
        organization_id=7,
    )

    assert total == 0
    session.execute.assert_awaited_once()
    statement = session.execute.await_args.args[0]
    _assert_query_shape(statement)


@pytest.mark.asyncio
async def test_count_campaign_usages_wraps_database_errors():
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=SQLAlchemyError("db failed"))
    repository = TemplateRepositoryImpl(session=session)

    with pytest.raises(ServerError) as exc:
        await repository.count_campaign_usages(
            template_id=55,
            organization_id=7,
        )

    assert str(exc.value.error) == "Failed to check template campaign usage"
    session.execute.assert_awaited_once()
