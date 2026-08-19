from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.settings import config
from src.core.utils.response import CustomResponse as cr
from src.core.utils.response import CustomSuccessResponseSchema
from src.modules.auth.infrastructure.models.user_model import UserModel
from src.modules.platform.application.access import (
    load_workspace_context,
    write_audit_log,
)
from src.modules.platform.infrastructure.models.platform_models import (
    SupportArticleModel,
    SupportTicketMessageModel,
    SupportTicketModel,
)
from src.modules.platform.presentation.schemas import (
    SupportTicketCreateRequest,
    SupportTicketMessageRequest,
)
from src.shared.dependencies.access_guard import require_access
from src.shared.exceptions.base_exceptions import InvalidError, NotFoundError
from src.shared.infrastructure.db import get_async_session

router = APIRouter(
    prefix="/support",
    dependencies=[Depends(require_access(authenticated=True, email_verified=True))],
)
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


def _article_payload(
    article: SupportArticleModel, include_content: bool = False
) -> dict:
    payload = {
        "uuid": article.uuid,
        "slug": article.slug,
        "title": article.title,
        "category": article.category,
        "summary": article.summary,
        "tags": article.tags,
        "updated_at": article.updated_at or article.created_at,
    }
    if include_content:
        payload["content"] = article.content
    return payload


def _ticket_payload(
    ticket: SupportTicketModel, created_by: UserModel | None = None
) -> dict:
    return {
        "uuid": ticket.uuid,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "resolution": ticket.resolution,
        "resolved_at": ticket.resolved_at,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "created_by": (
            {
                "uuid": created_by.uuid,
                "full_name": created_by.full_name,
                "email": created_by.email,
            }
            if created_by
            else None
        ),
    }


@router.get("/config", response_model=CustomSuccessResponseSchema)
async def support_config():
    return cr.success(
        data={
            "support_email": config.PUBLIC_SUPPORT_EMAIL,
            "chatboq_widget_url": config.CHATBOQ_WIDGET_URL,
        },
        message="Support configuration retrieved",
    )


@router.get("/articles", response_model=CustomSuccessResponseSchema)
async def list_articles(
    session: AsyncSessionDep,
    search: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    filters = [SupportArticleModel.is_published.is_(True)]
    if category:
        filters.append(SupportArticleModel.category == category.strip())
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                SupportArticleModel.title.ilike(pattern),
                SupportArticleModel.summary.ilike(pattern),
                SupportArticleModel.content.ilike(pattern),
            )
        )
    total = int(
        (
            await session.execute(
                select(func.count(SupportArticleModel.id)).where(*filters)
            )
        ).scalar()
        or 0
    )
    articles = (
        (
            await session.execute(
                select(SupportArticleModel)
                .where(*filters)
                .order_by(
                    SupportArticleModel.display_order.asc(),
                    SupportArticleModel.title.asc(),
                )
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    categories = (
        await session.execute(
            select(SupportArticleModel.category, func.count(SupportArticleModel.id))
            .where(SupportArticleModel.is_published.is_(True))
            .group_by(SupportArticleModel.category)
            .order_by(SupportArticleModel.category.asc())
        )
    ).all()
    return cr.success(
        data={
            "items": [_article_payload(article) for article in articles],
            "total": total,
            "categories": [
                {"name": name, "count": int(count)} for name, count in categories
            ],
        },
        message="Support articles retrieved",
    )


@router.get("/articles/{slug}", response_model=CustomSuccessResponseSchema)
async def get_article(slug: str, session: AsyncSessionDep):
    article = (
        (
            await session.execute(
                select(SupportArticleModel).where(
                    SupportArticleModel.slug == slug,
                    SupportArticleModel.is_published.is_(True),
                )
            )
        )
        .scalars()
        .first()
    )
    if not article:
        raise NotFoundError(error="Support article not found")
    return cr.success(
        data=_article_payload(article, include_content=True),
        message="Article retrieved",
    )


@router.get("/contextual-help", response_model=CustomSuccessResponseSchema)
async def contextual_help(
    session: AsyncSessionDep,
    context: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=5, ge=1, le=10),
):
    term = context.strip().lower()
    pattern = f"%{term}%"
    articles = (
        (
            await session.execute(
                select(SupportArticleModel)
                .where(
                    SupportArticleModel.is_published.is_(True),
                    or_(
                        SupportArticleModel.category.ilike(pattern),
                        SupportArticleModel.title.ilike(pattern),
                        SupportArticleModel.summary.ilike(pattern),
                    ),
                )
                .order_by(SupportArticleModel.display_order.asc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return cr.success(
        data={"items": [_article_payload(article) for article in articles]},
        message="Contextual help retrieved",
    )


@router.get("/tickets", response_model=CustomSuccessResponseSchema)
async def list_tickets(
    request: Request,
    session: AsyncSessionDep,
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    context = await load_workspace_context(request, session)
    filters = [SupportTicketModel.organization_id == context.organization.id]
    if status:
        filters.append(SupportTicketModel.status == status)
    total = int(
        (
            await session.execute(
                select(func.count(SupportTicketModel.id)).where(*filters)
            )
        ).scalar()
        or 0
    )
    tickets = (
        (
            await session.execute(
                select(SupportTicketModel)
                .where(*filters)
                .order_by(SupportTicketModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return cr.success(
        data={"items": [_ticket_payload(ticket) for ticket in tickets], "total": total},
        message="Support tickets retrieved",
    )


@router.post("/tickets", response_model=CustomSuccessResponseSchema)
async def create_ticket(
    request: Request,
    body: SupportTicketCreateRequest,
    session: AsyncSessionDep,
):
    context = await load_workspace_context(request, session)
    ticket = SupportTicketModel(
        organization_id=context.organization.id,
        created_by_id=request.state.user_id,
        subject=body.subject.strip(),
        description=body.description.strip(),
        category=body.category.strip().lower(),
        priority=body.priority,
        status="open",
    )
    session.add(ticket)
    await session.flush()
    await write_audit_log(
        session,
        request,
        action="support.ticket_created",
        resource_type="support_ticket",
        resource_uuid=ticket.uuid,
        metadata={"subject": ticket.subject, "priority": ticket.priority},
        organization_id=context.organization.id,
    )
    await session.commit()
    return cr.success(
        data=_ticket_payload(ticket), message="Support ticket created", status_code=201
    )


@router.get("/tickets/{ticket_uuid}", response_model=CustomSuccessResponseSchema)
async def get_ticket(request: Request, ticket_uuid: str, session: AsyncSessionDep):
    context = await load_workspace_context(request, session)
    result = await session.execute(
        select(SupportTicketModel, UserModel)
        .join(UserModel, UserModel.id == SupportTicketModel.created_by_id)
        .where(
            SupportTicketModel.uuid == ticket_uuid,
            SupportTicketModel.organization_id == context.organization.id,
        )
    )
    row = result.first()
    if not row:
        raise NotFoundError(error="Support ticket not found")
    ticket, creator = row
    messages = (
        await session.execute(
            select(SupportTicketMessageModel, UserModel)
            .outerjoin(
                UserModel, UserModel.id == SupportTicketMessageModel.author_user_id
            )
            .where(
                SupportTicketMessageModel.ticket_id == ticket.id,
                SupportTicketMessageModel.is_internal.is_(False),
            )
            .order_by(SupportTicketMessageModel.created_at.asc())
        )
    ).all()
    return cr.success(
        data={
            **_ticket_payload(ticket, creator),
            "messages": [
                {
                    "uuid": item.uuid,
                    "body": item.body,
                    "attachments": item.attachments,
                    "author": (
                        {"uuid": author.uuid, "full_name": author.full_name}
                        if author
                        else {"full_name": "MailTracko Support"}
                    ),
                    "created_at": item.created_at,
                }
                for item, author in messages
            ],
        },
        message="Support ticket retrieved",
    )


@router.post(
    "/tickets/{ticket_uuid}/messages", response_model=CustomSuccessResponseSchema
)
async def add_ticket_message(
    request: Request,
    ticket_uuid: str,
    body: SupportTicketMessageRequest,
    session: AsyncSessionDep,
):
    context = await load_workspace_context(request, session)
    if body.is_internal:
        raise InvalidError(
            error="Internal notes can only be added by platform administrators"
        )
    ticket = (
        (
            await session.execute(
                select(SupportTicketModel).where(
                    SupportTicketModel.uuid == ticket_uuid,
                    SupportTicketModel.organization_id == context.organization.id,
                )
            )
        )
        .scalars()
        .first()
    )
    if not ticket:
        raise NotFoundError(error="Support ticket not found")
    if ticket.status in {"resolved", "closed"}:
        ticket.status = "open"
        ticket.resolved_at = None
        ticket.resolution = None
    message = SupportTicketMessageModel(
        ticket_id=ticket.id,
        author_user_id=request.state.user_id,
        body=body.body.strip(),
        attachments=body.attachments,
        is_internal=False,
    )
    session.add(message)
    ticket.updated_at = datetime.now(UTC)
    await session.flush()
    await session.commit()
    return cr.success(
        data={
            "uuid": message.uuid,
            "body": message.body,
            "created_at": message.created_at,
        },
        message="Reply added",
        status_code=201,
    )


@router.post("/tickets/{ticket_uuid}/close", response_model=CustomSuccessResponseSchema)
async def close_ticket(request: Request, ticket_uuid: str, session: AsyncSessionDep):
    context = await load_workspace_context(request, session)
    ticket = (
        (
            await session.execute(
                select(SupportTicketModel).where(
                    SupportTicketModel.uuid == ticket_uuid,
                    SupportTicketModel.organization_id == context.organization.id,
                )
            )
        )
        .scalars()
        .first()
    )
    if not ticket:
        raise NotFoundError(error="Support ticket not found")
    ticket.status = "closed"
    ticket.resolved_at = ticket.resolved_at or datetime.now(UTC)
    await write_audit_log(
        session,
        request,
        action="support.ticket_closed",
        resource_type="support_ticket",
        resource_uuid=ticket.uuid,
        organization_id=context.organization.id,
    )
    await session.commit()
    return cr.success(
        data={"uuid": ticket.uuid, "status": ticket.status}, message="Ticket closed"
    )
