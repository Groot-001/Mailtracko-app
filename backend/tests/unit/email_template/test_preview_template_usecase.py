from unittest.mock import patch

import pytest


def _make_preview_payload(**overrides):
    from src.modules.email_template.presentation.schemas.template_schemas import (
        PreviewTemplateRequestSchema,
    )

    data = {
        "subject": "Hello {{first_name}} from {{company}}",
        "body_html": (
            "<p>Hello {{first_name}}</p>"
            "<p>Welcome to {{company}}</p>"
        ),
        "variables": {
            "first_name": "Sita",
            "company": "Mailtracko",
        },
    }
    data.update(overrides)

    return PreviewTemplateRequestSchema(**data)


@pytest.mark.asyncio
async def test_preview_template_usecase_renders_supplied_variables():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )

    usecase = PreviewTemplateUseCase()

    result = await usecase.execute(
        payload=_make_preview_payload(),
    )

    assert result["subject"] == "Hello Sita from Mailtracko"
    assert result["body_html"] == (
        "<p>Hello Sita</p><p>Welcome to Mailtracko</p>"
    )
    assert result["variables"] == [
        "first_name",
        "company",
    ]
    assert result["unresolved_variables"] == []


@pytest.mark.asyncio
async def test_preview_template_usecase_blanks_missing_variables_and_reports_unresolved():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )

    usecase = PreviewTemplateUseCase()

    result = await usecase.execute(
        payload=_make_preview_payload(
            variables={
                "first_name": "Sita",
            },
        ),
    )

    assert result["subject"] == "Hello Sita from "
    assert result["body_html"] == (
        "<p>Hello Sita</p>"
        "<p>Welcome to </p>"
    )
    assert result["variables"] == [
        "first_name",
        "company",
    ]
    assert result["unresolved_variables"] == [
        "company",
    ]


@pytest.mark.asyncio
async def test_preview_template_usecase_extracts_repeated_variables_once():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )

    usecase = PreviewTemplateUseCase()

    result = await usecase.execute(
        payload=_make_preview_payload(
            subject="Hello {{first_name}} {{first_name}}",
            body_html=(
                "<p>{{first_name}}</p>"
                "<p>{{company}}</p>"
                "<p>{{first_name}}</p>"
            ),
        ),
    )

    assert result["variables"] == [
        "first_name",
        "company",
    ]
    assert result["unresolved_variables"] == []


@pytest.mark.asyncio
async def test_preview_template_usecase_supports_nested_variables():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )

    usecase = PreviewTemplateUseCase()

    result = await usecase.execute(
        payload=_make_preview_payload(
            subject="Hello {{contact.first_name}}",
            body_html=(
                "<p>{{contact.first_name}} works at "
                "{{contact.company.name}}</p>"
            ),
            variables={
                "contact": {
                    "first_name": "Sita",
                    "company": {
                        "name": "Mailtracko",
                    },
                }
            },
        ),
    )

    assert result["subject"] == "Hello Sita"
    assert result["body_html"] == (
        "<p>Sita works at Mailtracko</p>"
    )
    assert result["variables"] == [
        "contact.first_name",
        "contact.company.name",
    ]
    assert result["unresolved_variables"] == []


@pytest.mark.asyncio
async def test_preview_template_usecase_prefers_exact_flat_key():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )

    usecase = PreviewTemplateUseCase()

    result = await usecase.execute(
        payload=_make_preview_payload(
            subject="Hello {{contact.first_name}}",
            body_html="<p>{{contact.first_name}}</p>",
            variables={
                "contact.first_name": "Flat Value",
                "contact": {
                    "first_name": "Nested Value",
                },
            },
        ),
    )

    assert result["subject"] == "Hello Flat Value"
    assert result["body_html"] == "<p>Flat Value</p>"


@pytest.mark.asyncio
async def test_preview_template_usecase_escapes_html_values_in_body():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )

    usecase = PreviewTemplateUseCase()

    unsafe_value = '<script>alert("x")</script>'

    result = await usecase.execute(
        payload=_make_preview_payload(
            subject="Hello {{first_name}}",
            body_html="<p>Hello {{first_name}}</p>",
            variables={
                "first_name": unsafe_value,
            },
        ),
    )

    assert result["subject"] == f"Hello {unsafe_value}"
    assert result["body_html"] == (
        "<p>Hello &lt;script&gt;"
        "alert(&quot;x&quot;)"
        "&lt;/script&gt;</p>"
    )


@pytest.mark.asyncio
async def test_preview_template_usecase_renders_none_as_empty_string():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )

    usecase = PreviewTemplateUseCase()

    result = await usecase.execute(
        payload=_make_preview_payload(
            subject="Hello {{first_name}}",
            body_html="<p>Hello {{first_name}}</p>",
            variables={
                "first_name": None,
            },
        ),
    )

    assert result["subject"] == "Hello "
    assert result["body_html"] == "<p>Hello </p>"
    assert result["variables"] == [
        "first_name",
    ]
    assert result["unresolved_variables"] == []


@pytest.mark.asyncio
async def test_preview_template_usecase_supports_custom_variable_names():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )

    usecase = PreviewTemplateUseCase()

    result = await usecase.execute(
        payload=_make_preview_payload(
            subject="Trip to {{travel-destination}}",
            body_html="<p>Code: {{custom_field_1}}</p>",
            variables={
                "travel-destination": "Pokhara",
                "custom_field_1": "ABC-101",
            },
        ),
    )

    assert result["subject"] == "Trip to Pokhara"
    assert result["body_html"] == (
        "<p>Code: ABC-101</p>"
    )
    assert result["variables"] == [
        "travel-destination",
        "custom_field_1",
    ]


@pytest.mark.asyncio
async def test_preview_template_usecase_ignores_invalid_placeholder_names():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )

    usecase = PreviewTemplateUseCase()

    result = await usecase.execute(
        payload=_make_preview_payload(
            subject="Hello {{123name}}",
            body_html="<p>{{first name}}</p>",
            variables={
                "123name": "Invalid",
                "first name": "Invalid",
            },
        ),
    )

    assert result["subject"] == "Hello {{123name}}"
    assert result["body_html"] == (
        "<p>{{first name}}</p>"
    )
    assert result["variables"] == []
    assert result["unresolved_variables"] == []


@pytest.mark.asyncio
async def test_preview_template_usecase_raises_for_blank_subject():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )
    from src.modules.email_template.presentation.schemas.template_schemas import (
        PreviewTemplateRequestSchema,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    payload = PreviewTemplateRequestSchema.model_construct(
        subject="   ",
        body_html="<p>Hello</p>",
        variables=None,
    )

    usecase = PreviewTemplateUseCase()

    with pytest.raises(InvalidError):
        await usecase.execute(
            payload=payload,
        )


@pytest.mark.asyncio
async def test_preview_template_usecase_raises_for_blank_body():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )
    from src.modules.email_template.presentation.schemas.template_schemas import (
        PreviewTemplateRequestSchema,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    payload = PreviewTemplateRequestSchema.model_construct(
        subject="Hello",
        body_html="   ",
        variables=None,
    )

    usecase = PreviewTemplateUseCase()

    with pytest.raises(InvalidError):
        await usecase.execute(
            payload=payload,
        )


@pytest.mark.asyncio
async def test_preview_template_usecase_wraps_unexpected_error():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    usecase = PreviewTemplateUseCase()

    with patch.object(
        usecase.template_rendering_service,
        "render_template",
        side_effect=RuntimeError(
            "Unexpected preview error",
        ),
    ):
        with pytest.raises(ServerError):
            await usecase.execute(
                payload=_make_preview_payload(),
            )

@pytest.mark.asyncio
async def test_preview_template_usecase_renders_fallback_values():
    from src.modules.email_template.application.usecases.core.preview_template_usecase import (
        PreviewTemplateUseCase,
    )

    usecase = PreviewTemplateUseCase()

    result = await usecase.execute(
        payload=_make_preview_payload(
            subject="Hello {{first_name|there}}",
            preheader="Welcome to {{company|Mailtracko}}",
            body_html=(
                "<p>Hello {{first_name|there}}</p>"
                "<p>Welcome to {{company|Mailtracko}}</p>"
            ),
            variables={
                "first_name": "",
            },
        ),
    )

    assert result["subject"] == "Hello there"
    assert result["preheader"] == "Welcome to Mailtracko"
    assert result["body_html"] == (
        "<p>Hello there</p>"
        "<p>Welcome to Mailtracko</p>"
    )
    assert result["fallback_variables"] == [
        "first_name",
        "company",
    ]
    assert result["unresolved_variables"] == []
