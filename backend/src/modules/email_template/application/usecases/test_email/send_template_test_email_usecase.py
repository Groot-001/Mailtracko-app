from src.modules.email_template.application.usecases.core.preview_template_usecase import (
    PreviewTemplateUseCase,
)
from src.modules.email_template.domain.services.template_rendering_service import (
    TemplateRenderingService,
)
from src.modules.email_template.infrastructure.email_sender.interface.test_email_sender_interface import (
    TestEmailMessage,
    TestEmailSenderInterface,
)
from src.modules.email_template.presentation.schemas.template_schemas import (
    PreviewTemplateRequestSchema,
    SendTemplateTestEmailRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ServerError,
)


class SendTemplateTestEmailUseCase:
    """
    Use case for sending current template editor content as a test email.
    """

    def __init__(
        self,
        preview_template_usecase: PreviewTemplateUseCase,
        test_email_sender: TestEmailSenderInterface,
        template_rendering_service: TemplateRenderingService | None = None,
    ):
        self.preview_template_usecase = (
            preview_template_usecase
        )
        self.test_email_sender = (
            test_email_sender
        )
        self.template_rendering_service = (
            template_rendering_service
            or TemplateRenderingService()
        )

    async def execute(
        self,
        *,
        payload: SendTemplateTestEmailRequestSchema,
        organization_id: int,
        actor_id: int,
    ) -> dict:
        """
        Renders supplied variables and sends the resulting test email.
        """
        try:
            preview_result = (
                await self.preview_template_usecase.execute(
                    payload=PreviewTemplateRequestSchema(
                        subject=payload.subject,
                        preheader=payload.preheader,
                        body_html=payload.body_html,
                        variables=payload.variables,
                    )
                )
            )

            body_text = (
                self.template_rendering_service.html_to_plain_text(
                    preview_result["body_html"]
                )
            )

            send_result = await self.test_email_sender.send(
                message=TestEmailMessage(
                    email_account_uuid=(
                        payload.email_account_uuid
                    ),
                    recipient_email=(
                        payload.recipient_email
                    ),
                    subject=preview_result["subject"],
                    preheader=preview_result[
                        "preheader"
                    ],
                    body_html=preview_result[
                        "body_html"
                    ],
                    body_text=body_text,
                    from_name=payload.from_name,
                ),
                organization_id=organization_id,
                actor_id=actor_id,
            )

            return {
                **send_result,
                "variables": preview_result[
                    "variables"
                ],
                "unresolved_variables": (
                    preview_result[
                        "unresolved_variables"
                    ]
                ),
                "fallback_variables": (
                    preview_result.get(
                        "fallback_variables",
                        [],
                    )
                ),
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "An error occurred while sending "
                    "template test email"
                ),
                internal_details=str(e),
            ) from e
