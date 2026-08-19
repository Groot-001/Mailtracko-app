from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.modules.email_template.application.usecases.core.preview_template_usecase import (
    PreviewTemplateUseCase,
)
from src.modules.email_template.application.usecases.test_email.send_template_test_email_usecase import (
    SendTemplateTestEmailUseCase,
)
from src.modules.email_template.domain.services.template_rendering_service import (
    TemplateRenderingService,
)
from src.modules.email_template.presentation.schemas.template_schemas import (
    SendTemplateTestEmailRequestSchema,
)


@pytest.mark.asyncio
async def test_test_send_uses_fallback_and_generated_plain_text():
    rendering_service = TemplateRenderingService()
    preview_usecase = PreviewTemplateUseCase(
        template_rendering_service=rendering_service,
    )
    sender = AsyncMock()
    sender.send.return_value = {
        "recipient_email": "receiver@example.com",
        "sender_email": "sender@example.com",
        "provider": "smtp",
        "sent_at": datetime.now(UTC),
    }

    usecase = SendTemplateTestEmailUseCase(
        preview_template_usecase=preview_usecase,
        test_email_sender=sender,
        template_rendering_service=rendering_service,
    )

    result = await usecase.execute(
        payload=SendTemplateTestEmailRequestSchema(
            email_account_uuid="account-uuid",
            recipient_email="receiver@example.com",
            subject="Hello {{first_name|there}}",
            preheader="Welcome to {{company|Mailtracko}}",
            body_html=(
                "<h1>Hello {{first_name|there}}</h1>"
                "<p>Your account is ready.</p>"
            ),
            variables={
                "first_name": "",
            },
        ),
        organization_id=10,
        actor_id=20,
    )

    sender.send.assert_awaited_once()
    message = sender.send.await_args.kwargs["message"]

    assert message.subject == "Hello there"
    assert message.preheader == "Welcome to Mailtracko"
    assert message.body_html == (
        "<h1>Hello there</h1>"
        "<p>Your account is ready.</p>"
    )
    assert message.body_text == (
        "Hello there\nYour account is ready."
    )
    assert result["fallback_variables"] == [
        "first_name",
        "company",
    ]
    assert result["unresolved_variables"] == []
