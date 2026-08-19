from src.modules.email_template.domain.services.template_rendering_service import (
    TemplateRenderingService,
)
from src.modules.email_template.presentation.schemas.template_schemas import (
    PreviewTemplateRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    InvalidError,
    ServerError,
)


class PreviewTemplateUseCase:
    """
    Use case for generating an email-template preview.
    """

    def __init__(
        self,
        template_rendering_service: TemplateRenderingService | None = None,
    ):
        self.template_rendering_service = (
            template_rendering_service
            or TemplateRenderingService()
        )

    async def execute(
        self,
        payload: PreviewTemplateRequestSchema,
    ) -> dict:
        """
        Renders the supplied subject, preheader, and HTML body without
        persistence.
        """
        try:
            self._validate_preview_content(
                subject=payload.subject,
                body_html=payload.body_html,
            )

            rendered_template = (
                self.template_rendering_service.render_template(
                    subject=payload.subject,
                    preheader=payload.preheader,
                    body_html=payload.body_html,
                    variables=payload.variables,
                )
            )

            return {
                "subject": rendered_template.subject,
                "preheader": rendered_template.preheader,
                "body_html": rendered_template.body_html,
                "variables": rendered_template.variables,
                "unresolved_variables": (
                    rendered_template.unresolved_variables
                ),
                "fallback_variables": (
                    rendered_template.fallback_variables
                ),
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "An error occurred while generating "
                    "template preview"
                ),
                internal_details=str(e),
            ) from e

    def _validate_preview_content(
        self,
        *,
        subject: str,
        body_html: str,
    ) -> None:
        """
        Validates required template preview content.
        """
        if not subject or not subject.strip():
            raise InvalidError(
                error=(
                    "Template subject is required for preview"
                )
            )

        if (
            not body_html
            or not body_html.strip()
        ):
            raise InvalidError(
                error=(
                    "Template body is required for preview"
                )
            )
