from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.modules.campaign.domain.enums import CampaignType, SequenceStepType, VariantType


def normalize_email(email: str) -> str:
    return email.strip().casefold()


_BLOCKED_CONTACT_STATUSES = frozenset({"bounced", "unsubscribed", "suppressed", "archived"})
_BLOCKED_VERIFICATION_STATUSES = frozenset({"invalid", "spamtrap", "abuse", "do_not_mail"})


def _has_sendable_email_syntax(email: str) -> bool:
    normalized = normalize_email(email)
    if not normalized or any(ch.isspace() for ch in normalized):
        return False
    if normalized.count("@") != 1:
        return False
    local, domain = normalized.rsplit("@", 1)
    if not local or not domain or "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return True


def campaign_contact_ineligibility_reason(
    *,
    email: str,
    subscribed: bool,
    status: str | None,
    verification_status: str | None,
    archived_at: object | None,
    suppressed: bool,
    bounce_risk: str | None,
) -> str | None:
    """Return why a contact must not receive a campaign, or ``None`` when sendable.

    Email verification is deliberately optional: unverified, valid, catch-all,
    risky, and unknown contacts remain eligible. Only contacts that are known to
    be unsafe/unavailable are excluded.
    """
    if not _has_sendable_email_syntax(email):
        return "invalid_email"
    if not subscribed:
        return "unsubscribed"
    normalized_status = str(status or "active").strip().lower()
    if archived_at is not None or normalized_status == "archived":
        return "archived"
    if suppressed or normalized_status == "suppressed":
        return "suppressed"
    if normalized_status == "bounced":
        return "bounced"
    verification = str(verification_status or "unverified").strip().lower()
    if verification in _BLOCKED_VERIFICATION_STATUSES:
        return "invalid"
    if str(bounce_risk or "").strip().lower() == "critical":
        return "invalid"
    if normalized_status in _BLOCKED_CONTACT_STATUSES:
        return normalized_status
    return None


def validate_timezone_name(timezone_name: str) -> str:
    """Return a normalized, valid IANA timezone name."""
    normalized = timezone_name.strip()
    if not normalized:
        raise ValueError("Campaign timezone is required")
    try:
        ZoneInfo(normalized)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Campaign timezone must be a valid IANA timezone") from exc
    return normalized


def normalize_sending_days(days: Sequence[int] | None) -> list[int]:
    """Normalize Python weekday numbers (Monday=0 ... Sunday=6)."""
    if days is None:
        return list(range(7))
    normalized = sorted(set(int(day) for day in days))
    if not normalized:
        raise ValueError("At least one sending day is required")
    if any(day < 0 or day > 6 for day in normalized):
        raise ValueError("Sending days must use values from 0 (Monday) to 6 (Sunday)")
    return normalized


def validate_sending_window(
    start: time | None,
    end: time | None,
    days: Sequence[int] | None,
) -> list[int]:
    """Validate a same-day sending window and return normalized weekdays."""
    normalized_days = normalize_sending_days(days)
    if (start is None) != (end is None):
        raise ValueError("Sending window start and end must be provided together")
    if start is not None and end is not None and start >= end:
        raise ValueError("Sending window end must be later than its start")
    return normalized_days


def is_within_sending_window(
    moment_utc: datetime,
    *,
    timezone_name: str,
    start: time | None,
    end: time | None,
    days: Sequence[int] | None,
) -> bool:
    if moment_utc.tzinfo is None:
        raise ValueError("The moment must include timezone information")
    timezone_name = validate_timezone_name(timezone_name)
    normalized_days = validate_sending_window(start, end, days)
    local_moment = moment_utc.astimezone(ZoneInfo(timezone_name))
    if local_moment.weekday() not in normalized_days:
        return False
    if start is None or end is None:
        return True
    local_time = local_moment.timetz().replace(tzinfo=None)
    return start <= local_time < end


def next_sending_window_at(
    moment_utc: datetime,
    *,
    timezone_name: str,
    start: time | None,
    end: time | None,
    days: Sequence[int] | None,
) -> datetime:
    """Return the next allowed send time in UTC without mutating campaign state."""
    if moment_utc.tzinfo is None:
        raise ValueError("The moment must include timezone information")
    timezone_name = validate_timezone_name(timezone_name)
    normalized_days = validate_sending_window(start, end, days)
    zone = ZoneInfo(timezone_name)
    local_moment = moment_utc.astimezone(zone)

    if is_within_sending_window(
        moment_utc,
        timezone_name=timezone_name,
        start=start,
        end=end,
        days=normalized_days,
    ):
        return moment_utc.astimezone(UTC)

    window_start = start or time.min
    for day_offset in range(0, 8):
        candidate_date = local_moment.date() + timedelta(days=day_offset)
        if candidate_date.weekday() not in normalized_days:
            continue
        candidate_local = datetime.combine(candidate_date, window_start, tzinfo=zone)
        if candidate_local <= local_moment:
            continue
        return candidate_local.astimezone(UTC)
    raise ValueError("Unable to calculate the next sending window")


def is_ab_test_sample_recipient(
    email: str,
    *,
    test_percentage: int,
    assignment_salt: str = "",
) -> bool:
    """Deterministically decide whether a recipient belongs to the A/B test sample."""
    percentage = int(test_percentage)
    if percentage <= 0 or percentage > 100:
        raise ValueError("A/B test percentage must be between 1 and 100")
    assignment_input = (
        f"{assignment_salt}:{normalize_email(email)}:sample".encode()
    )
    bucket = int(hashlib.sha256(assignment_input).hexdigest()[:8], 16) % 100
    return bucket < percentage


def choose_ab_variant(
    email: str,
    variants: Iterable[dict],
    *,
    assignment_salt: str = "",
) -> dict:
    """Deterministically assign an email to one weighted A/B variant using SHA-256."""
    ordered = sorted(variants, key=lambda item: item["variant_type"])
    if len(ordered) != 2:
        raise ValueError("A/B testing requires exactly two variants")

    total = sum(int(item["allocation_percentage"]) for item in ordered)
    if total != 100:
        raise ValueError("A/B variant allocation must total 100 percent")

    assignment_input = f"{assignment_salt}:{normalize_email(email)}".encode()
    bucket = int(hashlib.sha256(assignment_input).hexdigest()[:8], 16) % 100
    cursor = 0
    for variant in ordered:
        cursor += int(variant["allocation_percentage"])
        if bucket < cursor:
            return variant
    return ordered[-1]


def build_message_idempotency_key(
    *,
    campaign_uuid: str,
    recipient_uuid: str,
    step_order: int,
    variant_type: str | None,
) -> str:
    """Create a stable key for one logical campaign/recipient/step/variant send."""
    raw = ":".join(
        (
            campaign_uuid,
            recipient_uuid,
            str(step_order),
            variant_type or "regular",
        )
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def build_event_dedupe_key(
    *,
    campaign_uuid: str,
    recipient_uuid: str,
    event_type: str,
    provider_event_id: str | None,
    provider_message_id: str | None,
    custom_event_name: str | None,
) -> str:
    """Create a stable provider-event key; fallback events are unique per recipient/type."""
    event_identity = provider_event_id or provider_message_id or "single"
    raw = ":".join(
        (
            campaign_uuid,
            recipient_uuid,
            event_type,
            custom_event_name or "",
            event_identity,
        )
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def is_uncertain_send_exception(exc: Exception) -> bool:
    """Classify failures where retrying could duplicate an already accepted send."""
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    name = exc.__class__.__name__.casefold()
    module = exc.__class__.__module__.casefold()
    message = str(exc).casefold()
    return (
        "timeout" in name
        or "timeout" in message
        or "connectionreset" in name
        or "remoteprotocol" in name
        or ("httpx" in module and "connect" in name)
    )


def is_ab_winner_ready(
    *,
    sent_count: int,
    minimum_sample_size: int,
    test_duration_hours: int | None,
    started_at: datetime | None,
    now: datetime | None = None,
) -> bool:
    """Return true only after configured sample and duration rules are satisfied."""
    has_sample_rule = minimum_sample_size > 0
    has_duration_rule = test_duration_hours is not None
    if sent_count <= 0 or (not has_sample_rule and not has_duration_rule):
        return False
    if has_sample_rule and sent_count < minimum_sample_size:
        return False
    if has_duration_rule:
        if started_at is None:
            return False
        current = now or datetime.now(UTC)
        if current < started_at + timedelta(hours=int(test_duration_hours or 0)):
            return False
    return True


def validate_sequence_steps(steps: list[dict]) -> None:
    if not steps:
        raise ValueError("A sequence campaign requires at least one step")
    expected_orders = list(range(1, len(steps) + 1))
    actual_orders = sorted(int(step["step_order"]) for step in steps)
    if actual_orders != expected_orders:
        raise ValueError("Sequence step_order values must be consecutive and start at 1")
    if not any(step["step_type"] == SequenceStepType.EMAIL.value for step in steps):
        raise ValueError("A sequence requires at least one email step")

    for step in steps:
        step_type = step["step_type"]
        if step_type == SequenceStepType.EMAIL.value:
            if not step.get("template_id"):
                if not step.get("subject_override") or not step.get("body_html_override"):
                    raise ValueError(
                        "Every email step requires a template or subject/body overrides"
                    )
            if step.get("delay_value") is not None or step.get("delay_unit") is not None:
                raise ValueError("Email steps cannot contain delay fields")
        elif step_type == SequenceStepType.DELAY.value:
            if not step.get("delay_value") or int(step["delay_value"]) <= 0:
                raise ValueError("Delay steps require a positive delay_value")
            if not step.get("delay_unit"):
                raise ValueError("Delay steps require a delay_unit")
            if step.get("template_id") or step.get("subject_override") or step.get(
                "body_html_override"
            ):
                raise ValueError("Delay steps cannot contain email content")
        else:
            raise ValueError("Condition steps are not supported in the selected scope")


def validate_campaign_type_configuration(
    *,
    campaign_type: str,
    template_id: int | None,
    sequence_steps: list[dict],
    variants: list[dict],
) -> None:
    if campaign_type == CampaignType.REGULAR.value and template_id is None:
        raise ValueError("A regular campaign requires a template")
    if campaign_type == CampaignType.SEQUENCE.value:
        validate_sequence_steps(sequence_steps)
    if campaign_type == CampaignType.AB_TEST.value:
        variant_types = {item["variant_type"] for item in variants}
        if variant_types != {VariantType.A.value, VariantType.B.value}:
            raise ValueError("A/B testing requires variants A and B")
        choose_ab_variant("configuration-check@mailtracko.invalid", variants)
