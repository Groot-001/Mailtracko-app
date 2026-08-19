import re
from dataclasses import dataclass
from html import escape as escape_html
from html.parser import HTMLParser
from typing import Any


@dataclass(frozen=True, slots=True)
class RenderedTemplate:
    """
    Result produced after resolving template variables.
    """

    subject: str
    preheader: str | None
    body_html: str
    variables: list[str]
    unresolved_variables: list[str]
    fallback_variables: list[str]


class _HTMLToPlainTextParser(HTMLParser):
    """
    Converts email HTML into a readable plain-text alternative.
    """

    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "div",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "main",
        "nav",
        "p",
        "section",
        "table",
        "tr",
        "ul",
        "ol",
    }
    IGNORED_TAGS = {
        "head",
        "script",
        "style",
        "title",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0
        self.anchor_stack: list[tuple[str | None, int]] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        tag = tag.lower()

        if tag in self.IGNORED_TAGS:
            self.ignored_depth += 1
            return

        if self.ignored_depth:
            return

        if tag == "br":
            self._append_newline()
            return

        if tag == "li":
            self._append_newline()
            self.parts.append("- ")
            return

        if tag in self.BLOCK_TAGS:
            self._append_newline()

        if tag in {"td", "th"}:
            self._append_space()

        if tag == "a":
            href = dict(attrs).get("href")
            self.anchor_stack.append(
                (
                    href.strip() if href else None,
                    len(self.parts),
                )
            )

        if tag == "img":
            alt = dict(attrs).get("alt")
            if alt and alt.strip():
                self._append_space()
                self.parts.append(alt.strip())
                self._append_space()

    def handle_endtag(
        self,
        tag: str,
    ) -> None:
        tag = tag.lower()

        if tag in self.IGNORED_TAGS:
            if self.ignored_depth:
                self.ignored_depth -= 1
            return

        if self.ignored_depth:
            return

        if tag == "a" and self.anchor_stack:
            href, start_index = self.anchor_stack.pop()
            anchor_text = " ".join(
                "".join(
                    self.parts[start_index:]
                ).split()
            )
            del self.parts[start_index:]

            if anchor_text:
                self.parts.append(anchor_text)

            if href and href not in anchor_text:
                self.parts.append(f" ({href})")

        if tag == "li" or tag in self.BLOCK_TAGS:
            self._append_newline()

        if tag in {"td", "th"}:
            self._append_space()

    def handle_data(
        self,
        data: str,
    ) -> None:
        if self.ignored_depth or not data:
            return

        self.parts.append(data)

    def get_text(self) -> str:
        """
        Returns normalized plain text with meaningful line breaks.
        """
        raw_text = "".join(self.parts)
        raw_text = raw_text.replace("\r\n", "\n")
        raw_text = raw_text.replace("\r", "\n")
        raw_text = raw_text.replace("\xa0", " ")

        normalized_lines: list[str] = []
        previous_line_blank = False

        for raw_line in raw_text.split("\n"):
            line = re.sub(
                r"[ \t\f\v]+",
                " ",
                raw_line,
            ).strip()

            if not line:
                if normalized_lines and not previous_line_blank:
                    normalized_lines.append("")
                previous_line_blank = True
                continue

            normalized_lines.append(line)
            previous_line_blank = False

        while (
            normalized_lines
            and not normalized_lines[-1]
        ):
            normalized_lines.pop()

        return "\n".join(normalized_lines)

    def _append_newline(self) -> None:
        if not self.parts:
            return

        if not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def _append_space(self) -> None:
        if not self.parts:
            return

        if not self.parts[-1].endswith((" ", "\n", "\t")):
            self.parts.append(" ")


class TemplateRenderingService:
    """
    Resolves email-template variables and creates plain-text alternatives.
    """

    VARIABLE_PATTERN = re.compile(
        r"{{\s*"
        r"(?P<name>[a-zA-Z_][a-zA-Z0-9_.-]*)"
        r"\s*"
        r"(?:\|\s*(?P<fallback>[^{}]*?))?"
        r"\s*}}"
    )

    def render_template(
        self,
        *,
        subject: str,
        preheader: str | None,
        body_html: str,
        variables: dict[str, Any] | None,
    ) -> RenderedTemplate:
        """
        Renders all template content with one consistent variable policy.
        """
        supplied_variables = variables or {}

        detected_variables = self._extract_variables(
            subject=subject,
            preheader=preheader,
            body_html=body_html,
        )

        fallback_variables: list[str] = []
        fallback_variable_set: set[str] = set()
        unresolved_variables: list[str] = []
        unresolved_variable_set: set[str] = set()

        rendered_subject = self._render_content(
            content=subject,
            variables=supplied_variables,
            escape_values=False,
            fallback_variables=fallback_variables,
            fallback_variable_set=fallback_variable_set,
            unresolved_variables=unresolved_variables,
            unresolved_variable_set=unresolved_variable_set,
        )

        rendered_preheader = (
            self._render_content(
                content=preheader,
                variables=supplied_variables,
                escape_values=False,
                fallback_variables=fallback_variables,
                fallback_variable_set=fallback_variable_set,
                unresolved_variables=unresolved_variables,
                unresolved_variable_set=unresolved_variable_set,
            )
            if preheader is not None
            else None
        )

        rendered_body_html = self._render_content(
            content=body_html,
            variables=supplied_variables,
            escape_values=True,
            fallback_variables=fallback_variables,
            fallback_variable_set=fallback_variable_set,
            unresolved_variables=unresolved_variables,
            unresolved_variable_set=unresolved_variable_set,
        )

        return RenderedTemplate(
            subject=rendered_subject,
            preheader=rendered_preheader,
            body_html=rendered_body_html,
            variables=detected_variables,
            unresolved_variables=unresolved_variables,
            fallback_variables=fallback_variables,
        )

    def html_to_plain_text(
        self,
        body_html: str,
    ) -> str:
        """
        Generates a plain-text alternative from rendered HTML.
        """
        parser = _HTMLToPlainTextParser()
        parser.feed(body_html)
        parser.close()

        return parser.get_text()

    def _render_content(
        self,
        *,
        content: str,
        variables: dict[str, Any],
        escape_values: bool,
        fallback_variables: list[str],
        fallback_variable_set: set[str],
        unresolved_variables: list[str],
        unresolved_variable_set: set[str],
    ) -> str:
        """
        Resolves variables in one piece of template content.
        """

        def replace_variable(
            match: re.Match[str],
        ) -> str:
            variable_name = match.group("name")
            fallback_value = match.group("fallback")

            exists, value = self._resolve_variable(
                variable_name=variable_name,
                variables=variables,
            )

            if self._has_usable_value(
                exists=exists,
                value=value,
            ):
                return self._format_value(
                    value=value,
                    escape_values=escape_values,
                )

            if fallback_value is not None:
                self._append_unique(
                    value=variable_name,
                    values=fallback_variables,
                    seen_values=fallback_variable_set,
                )

                return self._format_value(
                    value=fallback_value.strip(),
                    escape_values=escape_values,
                )

            if exists:
                return self._format_value(
                    value="" if value is None else value,
                    escape_values=escape_values,
                )

            self._append_unique(
                value=variable_name,
                values=unresolved_variables,
                seen_values=unresolved_variable_set,
            )

            return ""

        return self.VARIABLE_PATTERN.sub(
            replace_variable,
            content,
        )

    def _extract_variables(
        self,
        *,
        subject: str,
        preheader: str | None,
        body_html: str,
    ) -> list[str]:
        """
        Extracts unique variable names while preserving content order.
        """
        detected_variables: list[str] = []
        seen_variables: set[str] = set()

        content = "\n".join(
            [
                subject,
                preheader or "",
                body_html,
            ]
        )

        for match in self.VARIABLE_PATTERN.finditer(content):
            self._append_unique(
                value=match.group("name"),
                values=detected_variables,
                seen_values=seen_variables,
            )

        return detected_variables

    def _resolve_variable(
        self,
        *,
        variable_name: str,
        variables: dict[str, Any],
    ) -> tuple[bool, Any]:
        """
        Resolves exact flat keys before nested dictionary paths.
        """
        if variable_name in variables:
            return True, variables[variable_name]

        current_value: Any = variables

        for key in variable_name.split("."):
            if not isinstance(current_value, dict):
                return False, None

            if key not in current_value:
                return False, None

            current_value = current_value[key]

        return True, current_value

    @staticmethod
    def _has_usable_value(
        *,
        exists: bool,
        value: Any,
    ) -> bool:
        if not exists or value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        return True

    @staticmethod
    def _format_value(
        *,
        value: Any,
        escape_values: bool,
    ) -> str:
        rendered_value = str(value)

        if escape_values:
            return escape_html(
                rendered_value,
                quote=True,
            )

        return rendered_value

    @staticmethod
    def _append_unique(
        *,
        value: str,
        values: list[str],
        seen_values: set[str],
    ) -> None:
        if value in seen_values:
            return

        seen_values.add(value)
        values.append(value)
