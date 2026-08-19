from src.modules.email_template.domain.services.template_rendering_service import (
    TemplateRenderingService,
)


def test_renderer_uses_fallback_for_missing_variable():
    service = TemplateRenderingService()

    result = service.render_template(
        subject="Hello {{first_name|there}}",
        preheader=None,
        body_html="<p>Hello {{first_name|there}}</p>",
        variables={},
    )

    assert result.subject == "Hello there"
    assert result.body_html == "<p>Hello there</p>"
    assert result.variables == ["first_name"]
    assert result.fallback_variables == ["first_name"]
    assert result.unresolved_variables == []


def test_renderer_uses_fallback_for_none_and_blank_values():
    service = TemplateRenderingService()

    result = service.render_template(
        subject=(
            "Hello {{first_name|there}} from "
            "{{company|your company}}"
        ),
        preheader=None,
        body_html=(
            "<p>{{first_name|there}} - "
            "{{company|your company}}</p>"
        ),
        variables={
            "first_name": None,
            "company": "   ",
        },
    )

    assert result.subject == "Hello there from your company"
    assert result.body_html == "<p>there - your company</p>"
    assert result.fallback_variables == [
        "first_name",
        "company",
    ]
    assert result.unresolved_variables == []


def test_renderer_does_not_use_fallback_when_value_exists():
    service = TemplateRenderingService()

    result = service.render_template(
        subject="Hello {{first_name|there}}",
        preheader="Welcome {{first_name|friend}}",
        body_html="<p>Hello {{first_name|there}}</p>",
        variables={"first_name": "Ram"},
    )

    assert result.subject == "Hello Ram"
    assert result.preheader == "Welcome Ram"
    assert result.body_html == "<p>Hello Ram</p>"
    assert result.fallback_variables == []
    assert result.unresolved_variables == []


def test_renderer_blanks_missing_variable_without_fallback_and_tracks_it():
    service = TemplateRenderingService()

    result = service.render_template(
        subject="Hello {{first_name}}",
        preheader=None,
        body_html="<p>Hello {{first_name}}</p>",
        variables={},
    )

    assert result.subject == "Hello "
    assert result.body_html == "<p>Hello </p>"
    assert result.fallback_variables == []
    assert result.unresolved_variables == ["first_name"]


def test_renderer_escapes_fallback_inside_html_body():
    service = TemplateRenderingService()

    result = service.render_template(
        subject="Hello {{first_name|<Guest>}}",
        preheader=None,
        body_html="<p>Hello {{first_name|<Guest>}}</p>",
        variables={},
    )

    assert result.subject == "Hello <Guest>"
    assert result.body_html == "<p>Hello &lt;Guest&gt;</p>"


def test_html_to_plain_text_preserves_content_and_links():
    service = TemplateRenderingService()

    plain_text = service.html_to_plain_text(
        """
        <html>
          <head><style>.hidden { display: none; }</style></head>
          <body>
            <h1>Hello Ram</h1>
            <p>Your account is <strong>ready</strong>.</p>
            <ul><li>First item</li><li>Second item</li></ul>
            <p><a href="https://example.com/unsubscribe">
              Unsubscribe
            </a></p>
          </body>
        </html>
        """
    )

    assert "Hello Ram" in plain_text
    assert "Your account is ready." in plain_text
    assert "- First item" in plain_text
    assert "- Second item" in plain_text
    assert (
        "Unsubscribe (https://example.com/unsubscribe)"
        in plain_text
    )
    assert ".hidden" not in plain_text
