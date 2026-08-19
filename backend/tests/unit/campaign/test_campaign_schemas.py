import pytest
from pydantic import ValidationError

from src.modules.campaign.presentation.schemas.campaign_schemas import (
    ConfigureABTestRequestSchema,
    ConfigureSequenceRequestSchema,
    CreateCampaignRequestSchema,
)


def test_create_campaign_schema_trims_name():
    payload = CreateCampaignRequestSchema(name="  Webinar Campaign  ")
    assert payload.name == "Webinar Campaign"


def test_sequence_schema_accepts_email_delay_email_flow():
    payload = ConfigureSequenceRequestSchema(
        steps=[
            {
                "step_order": 1,
                "step_type": "email",
                "subject_override": "Hello",
                "body_html_override": "<p>Hello</p>",
            },
            {
                "step_order": 2,
                "step_type": "delay",
                "delay_value": 2,
                "delay_unit": "days",
            },
            {
                "step_order": 3,
                "step_type": "email",
                "subject_override": "Follow up",
                "body_html_override": "<p>Following up</p>",
            },
        ]
    )
    assert len(payload.steps) == 3


def test_ab_test_requires_a_and_b_with_100_percent_allocation():
    payload = ConfigureABTestRequestSchema(
        variants=[
            {
                "variant_type": "a",
                "name": "Subject A",
                "subject_override": "A",
                "body_html_override": "<p>A</p>",
                "allocation_percentage": 50,
            },
            {
                "variant_type": "b",
                "name": "Subject B",
                "subject_override": "B",
                "body_html_override": "<p>B</p>",
                "allocation_percentage": 50,
            },
        ]
    )
    assert sum(item.allocation_percentage for item in payload.variants) == 100


def test_ab_test_rejects_invalid_allocation():
    with pytest.raises(ValidationError):
        ConfigureABTestRequestSchema(
            variants=[
                {
                    "variant_type": "a",
                    "name": "A",
                    "subject_override": "A",
                    "body_html_override": "<p>A</p>",
                    "allocation_percentage": 70,
                },
                {
                    "variant_type": "b",
                    "name": "B",
                    "subject_override": "B",
                    "body_html_override": "<p>B</p>",
                    "allocation_percentage": 20,
                },
            ]
        )


def test_sequence_allows_configurable_reply_stop_but_requires_unsubscribe_stop():
    payload = ConfigureSequenceRequestSchema(
        stop_on_reply=False,
        stop_on_unsubscribe=True,
        steps=[
            {
                "step_order": 1,
                "step_type": "email",
                "subject_override": "Hello",
                "body_html_override": "<p>Hello</p>",
            }
        ],
    )
    assert payload.stop_on_reply is False

    with pytest.raises(ValidationError):
        ConfigureSequenceRequestSchema(
            stop_on_unsubscribe=False,
            steps=[
                {
                    "step_order": 1,
                    "step_type": "email",
                    "subject_override": "Hello",
                    "body_html_override": "<p>Hello</p>",
                }
            ],
        )


def test_reconcile_send_schema_requires_provider_id_for_sent():
    from src.modules.campaign.presentation.schemas.campaign_schemas import (
        ReconcileSendOutcomeRequestSchema,
    )

    with pytest.raises(ValidationError):
        ReconcileSendOutcomeRequestSchema(outcome="sent")

    payload = ReconcileSendOutcomeRequestSchema(
        outcome="sent", provider_message_id="provider-123"
    )
    assert payload.provider_message_id == "provider-123"

def test_ab_response_supports_holdout_progress_fields() -> None:
    from src.modules.campaign.presentation.schemas.campaign_schemas import ABTestResponseSchema

    response = ABTestResponseSchema(
        uuid="ab-1",
        status="running",
        test_percentage=20,
        winner_metric="reply_rate",
        auto_select_winner=True,
        minimum_sample_size=10,
        sampled_recipient_count=20,
        holdout_recipient_count=80,
        released_recipient_count=0,
        variants=[],
    )
    assert response.sampled_recipient_count == 20
    assert response.holdout_recipient_count == 80

