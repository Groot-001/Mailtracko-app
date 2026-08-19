#!/usr/bin/env python3
"""Static contract checks for the user-reported MailTracko regression set.

These checks do not replace browser/integration tests. They ensure the root
contracts added for the reported bugs remain wired across FE/BE instead of
being lost during refactors.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def must(rel: str, *needles: str) -> None:
    text = read(rel)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{rel} missing: {missing}")


def must_not(rel: str, *needles: str) -> None:
    text = read(rel)
    present = [needle for needle in needles if needle in text]
    if present:
        raise AssertionError(f"{rel} still contains forbidden patterns: {present}")


def main() -> None:
    # #1 Pending invite timestamp + resend must be end-to-end.
    must(
        "frontend/src/feature/organization/components/team/PendingInvites.tsx",
        "invitation.updated_at ?? invitation.created_at",
        "Math.max(0, Date.now() - timestamp)",
        "useResendInvitation",
        "Resending…",
    )
    must(
        "backend/src/modules/organization/presentation/routers/organization_routers.py",
        '"/invitations/{invitation_uuid:str}/resend"',
        "ResendOrganizationInvitationResponseSchema",
    )
    must(
        "backend/src/modules/organization/application/usecases/core/resend_organization_invitation_usecase.py",
        "generate_invitation_token",
        "timedelta(days=7)",
        "OrganizationInvitationCreatedEvent",
        "raise_on_error=True",
    )

    # #2 Shared modal focus and collection form reset. No focus on dialog shell.
    must(
        "frontend/src/shared/components/Modal.tsx",
        '[data-autofocus="true"]',
        "focus:outline-none",
    )
    must_not("frontend/src/shared/components/Modal.tsx", "dialogRef.current?.focus")
    must(
        "frontend/src/feature/contacts/components/ContactsDashboard.tsx",
        "openCreateCollection",
        'data-autofocus="true"',
        "setNewListName('')",
        "setNewListDescription('')",
    )

    # #3 Decline always pins /login even if stale session cookie exists.
    must(
        "frontend/src/routes/invite/decline.tsx",
        "forceNextLoginScreen();",
        "clearPendingInvitationToken();",
        'navigate({ to: "/login", replace: true })',
    )
    must(
        "frontend/src/routes/invite/index.tsx",
        "forceNextLoginScreen();",
        "clearPendingInvitationToken();",
        'navigate({ to: "/login", replace: true })',
    )

    # #4/#6 Google Sheets OAuth/access: exact env callback, min scope, detailed failures.
    must(
        "backend/src/modules/contacts/infrastructure/oauth/google_sheets_oauth_client.py",
        'SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]',
        "config.GOOGLE_SHEETS_REDIRECT_URI",
        '"prompt": "consent"',
        '"include_granted_scopes": "true"',
        "Google Sheets API is not enabled",
        "Reconnect your Google account",
        "extract_sheet_id_from_url",
        'parsed.hostname != "docs.google.com"',
    )
    must(
        "frontend/src/feature/contacts/components/GoogleSheetsSync.tsx",
        "Reconnect Google",
        "Paste a valid Google Sheets URL",
    )

    # #5 Global dark mode + glow root cause.
    must(
        "frontend/src/index.css",
        "--mt-dark-text: #f8fafc",
        "Dark-mode legacy palette completion",
        "Hard-coded success/info/error colors",
        "Explicit legacy focus utilities are kept to one thin ring globally",
        ".mt-field-shell:has(> input:focus)",
    )
    must_not(
        "frontend/src/index.css",
        ':where(label, div)[class*="border"]:has(> input:focus)',
    )

    # #7 Merge tags preserve editor/textarea selection and side variables use the ref.
    must(
        "frontend/src/feature/templates/components/RichTextEditor.tsx",
        "savedRangeRef",
        "restoreSelection",
        'runCommand("insertText", `{{${normalized}}}`)',
        "textarea.selectionStart",
    )
    must(
        "frontend/src/feature/templates/components/TemplateContentStep.tsx",
        "editorRef.current?.insertMergeVariable(variable)",
    )

    # #8/#9/#10 Template + SMTP professional field styling/FE/BE inline validation.
    must(
        "frontend/src/feature/templates/schema/templateSchema.ts",
        "Template name is required.",
        "Subject line is required.",
        "Email body cannot be empty.",
        "Template name cannot exceed 50 characters.",
    )
    must(
        "frontend/src/feature/templates/components/TemplateWizard.tsx",
        "applyServerFieldErrors",
        "getApiFieldErrors",
    )
    must(
        "backend/src/modules/email_template/presentation/schemas/template_schemas.py",
        "Template name is required",
        "Subject line is required",
        "Email body cannot be empty",
    )
    must(
        "frontend/src/feature/email-accounts/components/SMTPFormModal.tsx",
        "zodResolver(smtpFormSchema)",
        "FieldError",
        "focus:ring-1",
        "attachBackendFieldErrors",
    )
    must(
        "backend/src/modules/email_account/presentation/schemas/email_account_schemas.py",
        "ge=1, le=65535",
        "SMTP host is required",
    )

    # #11/#12/#13 image URL, image upload and Code/source toggle.
    must(
        "frontend/src/feature/templates/components/RichTextEditor.tsx",
        "verifyRemoteImage",
        "valid public HTTPS image URL",
        "5 * 1024 * 1024",
        "resolveTemplateUuid",
        "uploadTemplateImage",
        "sourceMode",
        "Edit HTML source",
    )

    # #14 Stepwise wizard validation/publish gating.
    must(
        "frontend/src/feature/templates/components/TemplateWizard.tsx",
        "validateCurrentStep",
        "templateContentSchema",
        "templateSettingsSchema",
        "step !== steps.length - 1",
        "!isDraftValid",
    )

    # #15 Stable search (debounce + previous data).
    must(
        "frontend/src/feature/templates/hooks/useTemplates.ts",
        "keepPreviousData",
        "placeholderData: keepPreviousData",
    )
    must(
        "frontend/src/feature/templates/components/TemplateGalleryStep.tsx",
        "setTimeout(() => setSearch(searchInput.trim()), 250)",
        "galleryQuery.isFetching",
    )
    must(
        "frontend/src/feature/templates/components/TemplateDashboard.tsx",
        "const timer = window.setTimeout(() => {",
        "setSearch(searchInput.trim());",
        "}, 250);",
    )

    # #16 System template selection is a real copy flow, FE + BE.
    must(
        "frontend/src/feature/templates/components/TemplateGalleryStep.tsx",
        "copyMutation.mutateAsync(selectedUuid)",
        "onCopied(template)",
        "Use Selected Template",
    )
    must(
        "frontend/src/feature/templates/api/templateApi.ts",
        "/template-gallery/templates/${templateUuid}/copy",
    )
    must(
        "backend/src/modules/email_template/presentation/routers/email_template_routers.py",
        '"/template-gallery/templates/{template_uuid:str}/copy"',
    )

    # #17 New category autofocus.
    must(
        "frontend/src/feature/templates/components/TemplateSettingsStep.tsx",
        "categoryInputRef",
        "categoryInputRef.current?.focus",
    )

    # #18 SMTP leading zero normalization and numeric bounds.
    must(
        "frontend/src/feature/email-accounts/schema/smtpSchema.ts",
        'replace(/^0+(?=\\d)/, "")',
        "Port must be between 1 and 65535.",
    )

    # #19 Organization RHF/Zod, clearable optional values, cache sync and reset.
    must(
        "frontend/src/feature/organization/components/settings/OrganizationSettings.tsx",
        "zodResolver(organizationSettingsSchema)",
        "reset(defaultsFromOrganization(org))",
        "website_url: values.website_url.trim() || null",
        "domain_email: values.domain_email.trim().toLowerCase() || null",
        "reset(defaultsFromOrganization(updated))",
        "getApiFieldErrors",
    )
    must(
        "frontend/src/feature/organization/hooks/useOrganization.ts",
        "queryClient.setQueryData(ORGANIZATION_QUERY_KEY, updatedOrganization)",
    )
    must(
        "backend/src/modules/organization/presentation/schemas/organization_schemas.py",
        "Enter a valid website URL starting with http:// or https://",
        "Enter a valid company domain, for example yourcompany.com",
        "Enter a valid logo URL starting with http:// or https://",
    )

    # #20/#21 Preview/settings overflow containment.
    must(
        "frontend/src/shared/components/EmailPreviewFrame.tsx",
        "max-width: 100% !important",
        "overflow-x: auto",
        "min-w-0 max-w-full",
    )
    must(
        "frontend/src/feature/templates/components/TemplatePreviewStep.tsx",
        "min-w-0 overflow-hidden",
        "overflow-x-auto",
    )
    must(
        "frontend/src/feature/templates/components/TemplateSettingsStep.tsx",
        "grid min-w-0",
        "min-w-0 overflow-hidden",
    )

    # Earlier onboarding regression: every required step validates before advance,
    # and the server request schema remains authoritative at launch.
    must(
        "frontend/src/feature/onboarding/components/Step2Organization.tsx",
        "zodResolver(organizationStepSchema)",
        "handleSubmit(handleFormSubmit)",
    )
    for rel, schema_name in [
        ("frontend/src/feature/onboarding/components/Step3EmployeeCount.tsx", "emailVolumeStepSchema.safeParse"),
        ("frontend/src/feature/onboarding/components/Step4IndustrySector.tsx", "industrySectorStepSchema.safeParse"),
        ("frontend/src/feature/onboarding/components/Step5SourceDiscovery.tsx", "sourceStepSchema.safeParse"),
        ("frontend/src/feature/onboarding/components/Step6ThemeSelection.tsx", "themeStepSchema.safeParse"),
    ]:
        must(rel, schema_name)
    must(
        "frontend/src/feature/onboarding/components/OnboardingLayout.tsx",
        "validationSteps",
        "onboarding.setStep(invalid.step)",
    )
    must(
        "backend/src/modules/organization/presentation/schemas/organization_schemas.py",
        "Monthly email volume is required",
        "Industry sector is required",
    )

    print("PASS: all user-reported bug contracts are present (21 tracked + onboarding regression).")


if __name__ == "__main__":
    main()
