import pytest

from src.modules.campaign.domain.entities import Campaign, CampaignAudience
from src.modules.campaign.domain.enums import CampaignStatus
from src.modules.campaign.domain.services import (
    choose_ab_variant,
    is_ab_test_sample_recipient,
    normalize_email,
    build_event_dedupe_key,
    build_message_idempotency_key,
    is_within_sending_window,
    next_sending_window_at,
    validate_sequence_steps,
    validate_timezone_name,
    campaign_contact_ineligibility_reason,
)


def test_campaign_uses_integer_internal_id_and_string_public_uuid():
    campaign = Campaign(organization_id=10, name=" Product Launch ")

    assert campaign.id is None
    assert isinstance(campaign.uuid, str)
    assert campaign.name == "Product Launch"


def test_campaign_status_transition_rules():
    campaign = Campaign(organization_id=10, name="Product Launch")

    campaign.transition_to(CampaignStatus.READY)
    campaign.transition_to(CampaignStatus.LAUNCHING)
    campaign.transition_to(CampaignStatus.RUNNING)
    campaign.transition_to(CampaignStatus.PAUSED)
    campaign.transition_to(CampaignStatus.RUNNING)
    campaign.transition_to(CampaignStatus.COMPLETED)

    assert campaign.status == CampaignStatus.COMPLETED.value
    assert campaign.completed_at is not None


def test_invalid_campaign_transition_is_rejected():
    campaign = Campaign(organization_id=10, name="Product Launch")

    with pytest.raises(ValueError):
        campaign.transition_to(CampaignStatus.COMPLETED)


def test_campaign_audience_final_count():
    audience = CampaignAudience(
        estimated_recipient_count=100,
        duplicate_contacts_removed=5,
        excluded_contacts_count=10,
    )

    assert audience.final_recipient_count == 85


def test_email_normalization_and_ab_assignment_are_deterministic():
    variants = [
        {"variant_type": "a", "allocation_percentage": 50},
        {"variant_type": "b", "allocation_percentage": 50},
    ]

    first = choose_ab_variant(" User@Example.com ", variants)
    second = choose_ab_variant("user@example.com", variants)

    assert normalize_email(" User@Example.com ") == "user@example.com"
    assert first == second


def test_sequence_requires_consecutive_steps_and_email_content():
    steps = [
        {
            "step_order": 1,
            "step_type": "email",
            "template_id": 22,
            "subject_override": None,
            "body_html_override": None,
            "delay_value": None,
        },
        {
            "step_order": 2,
            "step_type": "delay",
            "template_id": None,
            "subject_override": None,
            "body_html_override": None,
            "delay_value": 1,
            "delay_unit": "days",
        },
    ]

    validate_sequence_steps(steps)

    steps[1]["step_order"] = 3
    with pytest.raises(ValueError):
        validate_sequence_steps(steps)


def test_campaign_timezone_and_sending_window_are_validated():
    campaign = Campaign(
        organization_id=10,
        name="Timed Campaign",
        timezone="Asia/Kathmandu",
        sending_window_start=__import__("datetime").time(9, 0),
        sending_window_end=__import__("datetime").time(17, 0),
        sending_days=[0, 1, 2, 3, 4],
    )

    assert campaign.timezone == "Asia/Kathmandu"
    assert campaign.sending_days == [0, 1, 2, 3, 4]
    assert validate_timezone_name("UTC") == "UTC"


def test_sending_window_calculation_uses_campaign_timezone():
    from datetime import UTC, datetime, time

    inside = datetime(2026, 7, 27, 4, 0, tzinfo=UTC)  # 09:45 in Kathmandu.
    outside = datetime(2026, 7, 27, 0, 0, tzinfo=UTC)

    assert is_within_sending_window(
        inside,
        timezone_name="Asia/Kathmandu",
        start=time(9, 0),
        end=time(17, 0),
        days=[0, 1, 2, 3, 4],
    )
    assert next_sending_window_at(
        outside,
        timezone_name="Asia/Kathmandu",
        start=time(9, 0),
        end=time(17, 0),
        days=[0, 1, 2, 3, 4],
    ) == datetime(2026, 7, 27, 3, 15, tzinfo=UTC)


def test_idempotency_and_event_keys_are_stable():
    first_message_key = build_message_idempotency_key(
        campaign_uuid="campaign-1",
        recipient_uuid="recipient-1",
        step_order=2,
        variant_type="a",
    )
    second_message_key = build_message_idempotency_key(
        campaign_uuid="campaign-1",
        recipient_uuid="recipient-1",
        step_order=2,
        variant_type="a",
    )
    first_event_key = build_event_dedupe_key(
        campaign_uuid="campaign-1",
        recipient_uuid="recipient-1",
        event_type="opened",
        provider_event_id="provider-event-1",
        provider_message_id=None,
        custom_event_name=None,
    )
    second_event_key = build_event_dedupe_key(
        campaign_uuid="campaign-1",
        recipient_uuid="recipient-1",
        event_type="opened",
        provider_event_id="provider-event-1",
        provider_message_id=None,
        custom_event_name=None,
    )

    assert first_message_key == second_message_key
    assert first_event_key == second_event_key
    assert len(first_message_key) == 64
    assert len(first_event_key) == 64



def test_uncertain_send_detection_is_fail_closed_for_timeouts():
    from src.modules.campaign.domain.services import is_uncertain_send_exception

    assert is_uncertain_send_exception(TimeoutError("provider timeout"))
    assert is_uncertain_send_exception(ConnectionResetError("connection reset"))
    assert not is_uncertain_send_exception(ValueError("bad address"))


def test_ab_winner_readiness_respects_sample_duration_and_requires_sends():
    from datetime import UTC, datetime, timedelta

    from src.modules.campaign.domain.services import is_ab_winner_ready

    started_at = datetime.now(UTC) - timedelta(hours=3)
    assert is_ab_winner_ready(
        sent_count=10,
        minimum_sample_size=10,
        test_duration_hours=2,
        started_at=started_at,
    )
    assert not is_ab_winner_ready(
        sent_count=5,
        minimum_sample_size=10,
        test_duration_hours=2,
        started_at=started_at,
    )
    assert not is_ab_winner_ready(
        sent_count=0,
        minimum_sample_size=0,
        test_duration_hours=2,
        started_at=started_at,
    )

def test_ab_sample_assignment_is_stable_and_respects_full_sample() -> None:
    first = is_ab_test_sample_recipient(
        "Sample@Example.com", test_percentage=25, assignment_salt="campaign-1"
    )
    second = is_ab_test_sample_recipient(
        "sample@example.com", test_percentage=25, assignment_salt="campaign-1"
    )
    assert first is second
    assert is_ab_test_sample_recipient(
        "any@example.com", test_percentage=100, assignment_salt="campaign-1"
    )


def test_ab_sample_assignment_rejects_invalid_percentage() -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        is_ab_test_sample_recipient("sample@example.com", test_percentage=0)



def test_campaign_contact_verification_is_optional_but_known_bad_contacts_are_blocked():
    base = {
        "email": "person@example.com",
        "subscribed": True,
        "status": "active",
        "archived_at": None,
        "suppressed": False,
        "bounce_risk": None,
    }

    for verification_status in (None, "unverified", "valid", "catch-all", "unknown", "risky"):
        assert campaign_contact_ineligibility_reason(
            **base, verification_status=verification_status
        ) is None

    for verification_status in ("invalid", "spamtrap", "abuse", "do_not_mail"):
        assert campaign_contact_ineligibility_reason(
            **base, verification_status=verification_status
        ) == "invalid"

    assert campaign_contact_ineligibility_reason(
        **{**base, "email": "not-an-email"}, verification_status="unverified"
    ) == "invalid_email"
    assert campaign_contact_ineligibility_reason(
        **{**base, "subscribed": False}, verification_status="unverified"
    ) == "unsubscribed"
    assert campaign_contact_ineligibility_reason(
        **{**base, "status": "archived"}, verification_status="unverified"
    ) == "archived"
    assert campaign_contact_ineligibility_reason(
        **{**base, "status": "bounced"}, verification_status="unverified"
    ) == "bounced"
    assert campaign_contact_ineligibility_reason(
        **{**base, "suppressed": True}, verification_status="unverified"
    ) == "suppressed"
    assert campaign_contact_ineligibility_reason(
        **{**base, "bounce_risk": "critical"}, verification_status="unverified"
    ) == "invalid"
