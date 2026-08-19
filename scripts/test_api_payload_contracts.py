#!/usr/bin/env python3
"""Validate representative frontend request payloads against backend schemas."""
from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from src.modules.auth.presentation.schemas.auth_schemas import RegisterRequest
from src.modules.campaign.presentation.schemas.campaign_schemas import (
    ConfigureABTestRequestSchema,
    ConfigureSequenceRequestSchema,
    CreateCampaignRequestSchema,
    ScheduleCampaignRequestSchema,
    UpdateCampaignRequestSchema,
)
from src.modules.contacts.presentation.schemas.contact_list_schemas import CreateContactListRequestSchema
from src.modules.email_account.presentation.schemas.email_account_schemas import ConnectSmtpRequestSchema
from src.modules.email_template.presentation.schemas.template_schemas import (
    CreateTemplateRequestSchema,
    PreviewTemplateRequestSchema,
    SendTemplateTestEmailRequestSchema,
    UpdateTemplateRequestSchema,
)
from src.modules.platform.presentation.schemas import ApiKeyCreateRequest, WebhookCreateRequest
from src.modules.organization.presentation.schemas.organization_schemas import (
    AcceptOrganizationInvitationRequestSchema,
    CreateOrganizationRequestSchema,
    DeclineOrganizationInvitationRequestSchema,
)

checks = 0


def validate(schema, payload):
    global checks
    model = schema.model_validate(payload)
    checks += 1
    return model


def reject(schema, payload):
    global checks
    try:
        schema.model_validate(payload)
    except ValidationError:
        checks += 1
        return
    raise AssertionError(f"{schema.__name__} unexpectedly accepted an invalid payload: {payload}")


validate(
    CreateTemplateRequestSchema,
    {
        "name": "Phase 1 Welcome",
        "subject": "Welcome {{first_name}}",
        "body_html": "<p>Hello {{first_name}}, welcome to MailTracko.</p>",
        "description": "A reusable welcome template",
        "preheader": "Welcome aboard",
        "from_name": "MailTracko Team",
        "from_email": "sender@example.com",
        "category_id": 1,
        "tags": ["welcome", "phase-1"],
        "is_default": False,
        "smart_personalization_enabled": False,
    },
)
validate(
    UpdateTemplateRequestSchema,
    {
        "subject": "Updated subject",
        "body_html": "<p>Updated email content.</p>",
        "tags": [],
    },
)
validate(
    PreviewTemplateRequestSchema,
    {
        "subject": "Hello {{first_name}}",
        "body_html": "<p>Hello {{first_name}}</p>",
        "preheader": None,
        "variables": {"first_name": "Alex"},
    },
)
validate(
    SendTemplateTestEmailRequestSchema,
    {
        "email_account_uuid": "account-uuid",
        "recipient_email": "test@example.com",
        "subject": "Test email",
        "body_html": "<p>Test message</p>",
        "preheader": None,
        "from_name": "MailTracko",
        "variables": {},
    },
)

base_campaign = {
    "name": "Phase 1 Outreach",
    "description": "Integrated frontend contract",
    "campaign_type": "regular",
    "goal": "outreach",
    "priority": "normal",
    "timezone": "Asia/Kathmandu",
    "email_account_uuid": "account-uuid",
    "template_uuid": "template-uuid",
    "contact_list_uuid": "list-uuid",
    "daily_limit": 100,
    "batch_size": 25,
}
validate(CreateCampaignRequestSchema, base_campaign)
validate(
    UpdateCampaignRequestSchema,
    {
        "current_step": "content",
        "timezone": "Asia/Kathmandu",
        "sending_window_start": None,
        "sending_window_end": None,
        "sending_days": [0, 1, 2, 3, 4],
        "daily_limit": 100,
        "batch_size": 25,
    },
)
validate(
    ConfigureSequenceRequestSchema,
    {
        "stop_on_reply": True,
        "stop_on_unsubscribe": True,
        "stop_on_click": False,
        "stop_on_meeting": False,
        "custom_stop_events": [],
        "steps": [
            {
                "step_order": 1,
                "step_type": "email",
                "template_uuid": "template-uuid",
                "subject_override": None,
                "body_html_override": None,
                "delay_value": None,
                "delay_unit": None,
                "is_enabled": True,
            },
            {
                "step_order": 2,
                "step_type": "delay",
                "template_uuid": None,
                "subject_override": None,
                "body_html_override": None,
                "delay_value": 2,
                "delay_unit": "days",
                "is_enabled": True,
            },
        ],
    },
)
validate(
    ConfigureABTestRequestSchema,
    {
        "test_percentage": 100,
        "winner_metric": "reply_rate",
        "auto_select_winner": False,
        "minimum_sample_size": 0,
        "test_duration_hours": None,
        "variants": [
            {
                "variant_type": "a",
                "name": "Variant A",
                "template_uuid": "template-a",
                "subject_override": None,
                "body_html_override": None,
                "allocation_percentage": 50,
            },
            {
                "variant_type": "b",
                "name": "Variant B",
                "template_uuid": "template-b",
                "subject_override": None,
                "body_html_override": None,
                "allocation_percentage": 50,
            },
        ],
    },
)
validate(
    ScheduleCampaignRequestSchema,
    {
        "scheduled_at": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
        "timezone": "Asia/Kathmandu",
    },
)
validate(
    RegisterRequest,
    {
        "full_name": "Invited User",
        "email": "invitee@example.com",
        "password": "StrongPassword!123",
        "invite_token": "secure-invitation-token",
    },
)
validate(AcceptOrganizationInvitationRequestSchema, {"token": "secure-invitation-token"})
validate(DeclineOrganizationInvitationRequestSchema, {"token": "secure-invitation-token"})


# QA Bug #9: name/title-style fields are capped at 50 characters in the API, not just the UI.
reject(CreateContactListRequestSchema, {"name": "x" * 51})
reject(CreateCampaignRequestSchema, {**base_campaign, "name": "x" * 51})
reject(CreateTemplateRequestSchema, {"name": "x" * 51, "subject": "Subject", "body_html": "<p>Body</p>"})
reject(RegisterRequest, {"full_name": "x" * 51, "email": "qa@example.com", "password": "StrongPassword!123"})
reject(CreateOrganizationRequestSchema, {"name": "x" * 51})

reject(
    ConnectSmtpRequestSchema,
    {
        "email": "sender@example.com",
        "sender_name": "x" * 51,
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "sender@example.com",
        "smtp_password": "secret",
    },
)
reject(ApiKeyCreateRequest, {"name": "x" * 51, "scopes": []})
reject(
    WebhookCreateRequest,
    {"name": "x" * 51, "url": "https://example.com/hooks/mailtracko", "events": ["campaign.completed"]},
)

print(f"Representative API payload validation passed: {checks} schemas.")
