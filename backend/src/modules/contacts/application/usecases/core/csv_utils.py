import csv
import io
import re

from src.shared.exceptions.base_exceptions import DomainError

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


# Canonical columns of the downloadable CSV import template. Google Sheet imports
# must contain every one of these headers so the sheet is consistent with the template.
CSV_TEMPLATE_FIELDS = [
    "email",
    "first_name",
    "last_name",
    "company",
    "phone",
    "city",
    "state",
    "country",
]


KNOWN_FIELDS = set()


_HEADER_ALIASES = {
    "email": "email",
    "emailaddress": "email",
    "emailid": "email",
    "e-mail": "email",
    "mail": "email",
    "name": "name",
    "fullname": "name",
    "contactname": "name",
    "firstname": "first_name",
    "givenname": "first_name",
    "lastname": "last_name",
    "surname": "last_name",
    "familyname": "last_name",
    "company": "company",
    "companyname": "company",
    "organization": "company",
    "organisation": "company",
    "business": "company",
    "phone": "phone",
    "phonenumber": "phone",
    "mobile": "phone",
    "mobilenumber": "phone",
    "city": "city",
    "state": "state",
    "province": "state",
    "country": "country",
    "jobtitle": "job_title",
    "title": "job_title",
    "website": "website",
    "location": "location",
}


def normalize_import_header(value: str) -> str:
    """Normalize common CSV/Sheets headings to MailTracko contact metadata keys.

    Unknown headings are preserved in a stable snake_case form so imports never lose
    custom columns while common headings such as "Email Address" and "Company Name"
    work without manual cleanup.
    """
    raw = (value or "").strip()
    compact = re.sub(r"[^a-z0-9-]+", "", raw.lower())
    if compact in _HEADER_ALIASES:
        return _HEADER_ALIASES[compact]

    snake = re.sub(r"[^a-zA-Z0-9]+", "_", raw).strip("_").lower()
    return snake or "field"


def decode_csv(csv_content: bytes) -> str:
    try:
        return csv_content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            return csv_content.decode("latin-1")
        except Exception:
            raise DomainError(
                error="CSV file encoding is not supported. Please upload a UTF-8 encoded CSV file."
            )


def parse_rows(content_str: str) -> tuple[list[dict], list[dict], dict, list[str]]:
    reader = csv.DictReader(io.StringIO(content_str))
    raw_fieldnames = [str(name or "").strip() for name in (reader.fieldnames or [])]
    if not raw_fieldnames:
        raise DomainError(error="CSV file does not contain a header row")

    header_mapping: dict[str, str] = {}
    normalized_by_raw: dict[str, str] = {}
    used_headers: dict[str, int] = {}
    for index, raw_name in enumerate(raw_fieldnames, start=1):
        source_name = raw_name or f"Column {index}"
        normalized = normalize_import_header(source_name)
        occurrence = used_headers.get(normalized, 0) + 1
        used_headers[normalized] = occurrence
        target_name = normalized if occurrence == 1 else f"{normalized}_{occurrence}"
        header_mapping[source_name] = target_name
        normalized_by_raw[raw_name] = target_name

    if "email" not in normalized_by_raw.values():
        raise DomainError(
            error="CSV must contain an email column (for example Email or Email Address)"
        )

    extra_fields = [
        target_name
        for target_name in normalized_by_raw.values()
        if target_name != "email"
    ]

    parsed_rows: list[dict] = []
    error_rows: list[dict] = []

    for i, row in enumerate(reader):
        email_val = ""
        metadata: dict[str, str] = {}

        for raw_key, raw_value in row.items():
            if raw_key is None:
                continue
            clean_key = str(raw_key).strip()
            target_key = normalized_by_raw.get(clean_key, normalize_import_header(clean_key))
            value = str(raw_value or "").strip()
            if target_key == "email":
                email_val = value.lower()
            elif value:
                metadata[target_key] = value

        if not email_val:
            error_rows.append({"row": i + 2, "error": "Missing email"})
            continue

        if not _EMAIL_RE.match(email_val):
            error_rows.append(
                {"row": i + 2, "error": f"Invalid email format: {email_val}"}
            )
            continue

        parsed_rows.append(
            {
                "email": email_val,
                "metadata_dict": metadata or None,
            }
        )

    return parsed_rows, error_rows, header_mapping, extra_fields
