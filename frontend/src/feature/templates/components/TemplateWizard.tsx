import { useMemo, useRef, useState } from "react";
import { Link, useBlocker, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, ArrowRight, Check, Save, Send } from "lucide-react";
import { InlineNotice } from "../../../shared/components/InlineNotice";
import { ConfirmDialog } from "../../../shared/components/ConfirmDialog";
import { PageContainer } from "../../../shared/components/layout";
import { useToast } from "../../../shared/hooks/useToast";
import { getApiErrorMessage, getApiFieldErrors } from "../../../shared/utils/apiError";
import {
  useCreateTemplate,
  usePublishTemplate,
  useTemplate,
  useTemplateCategories,
  useUpdateTemplate,
} from "../hooks/useTemplates";
import type { EmailTemplate, EmailTemplateDetail, TemplatePayload } from "../types/template.types";
import { TemplateContentStep } from "./TemplateContentStep";
import { TemplateGalleryStep } from "./TemplateGalleryStep";
import { TemplatePreviewStep } from "./TemplatePreviewStep";
import { TemplateReviewStep } from "./TemplateReviewStep";
import { TemplateSettingsStep } from "./TemplateSettingsStep";
import {
  getTemplateFieldErrors,
  templateContentSchema,
  templateDraftSchema,
  templateSettingsSchema,
  type TemplateFieldErrors,
} from "../schema/templateSchema";

export interface TemplateDraft {
  name: string;
  subject: string;
  body_html: string;
  description: string;
  preheader: string;
  from_name: string;
  from_email: string;
  category_id: number | null;
  tags: string[];
  is_default: boolean;
}

interface TemplateWizardProps {
  templateUuid?: string;
}

const blankTemplate: TemplateDraft = {
  name: "",
  subject: "",
  body_html:
    "<h2>Welcome, {{first_name}}!</h2><p>Thanks for connecting with us.</p><p>Use this space to create a clear and useful message for your recipients.</p><p><a href=\"{{unsubscribe_link}}\">Unsubscribe</a></p>",
  description: "",
  preheader: "",
  from_name: "",
  from_email: "",
  category_id: null,
  tags: [],
  is_default: false,
};

const steps = ["Choose", "Content", "Settings", "Preview", "Review"] as const;

const toDraft = (template: EmailTemplateDetail): TemplateDraft => ({
  name: template.name,
  subject: template.subject,
  body_html: template.body_html ?? "",
  description: template.description ?? "",
  preheader: template.preheader ?? "",
  from_name: template.from_name ?? "",
  from_email: template.from_email ?? "",
  category_id: template.category_id,
  tags: template.tags,
  is_default: template.is_default,
});

interface TemplateDraftOverride {
  identity: string;
  value: TemplateDraft;
}

export const TemplateWizard = ({ templateUuid }: TemplateWizardProps) => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const allowNavigationRef = useRef(false);
  const editing = Boolean(templateUuid);
  const templateQuery = useTemplate(templateUuid ?? "");
  const categoriesQuery = useTemplateCategories();
  const createMutation = useCreateTemplate();
  const updateMutation = useUpdateTemplate();
  const publishMutation = usePublishTemplate();
  const [step, setStep] = useState(editing ? 1 : 0);
  const [draftOverride, setDraftOverride] = useState<TemplateDraftOverride | null>(null);
  const [createdTemplateUuid, setCreatedTemplateUuid] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<TemplateFieldErrors>({});
  const [feedback, setFeedback] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  const activeTemplateIdentity = templateUuid ?? "create";
  const sourceDraft: TemplateDraft = editing
    ? templateQuery.data
      ? toDraft(templateQuery.data)
      : blankTemplate
    : blankTemplate;
  const effectiveDraft = draftOverride?.identity === activeTemplateIdentity
    ? draftOverride.value
    : sourceDraft;
  const persistedTemplateUuid = templateUuid ?? createdTemplateUuid ?? undefined;
  const isDirty = Boolean(
    draftOverride?.identity === activeTemplateIdentity &&
    JSON.stringify(effectiveDraft) !== JSON.stringify(sourceDraft),
  );

  // TanStack Router also installs the native beforeunload fallback for refresh/tab close.
  const blocker = useBlocker({
    shouldBlockFn: () => isDirty && !allowNavigationRef.current,
    enableBeforeUnload: () => isDirty && !allowNavigationRef.current,
    withResolver: true,
  });

  const categoryName = useMemo(
    () => categoriesQuery.data?.find((category) => category.id === effectiveDraft.category_id)?.name,
    [categoriesQuery.data, effectiveDraft.category_id],
  );
  const loadedTemplateStatus = editing ? templateQuery.data?.status : null;
  const editingLocked = Boolean(editing && loadedTemplateStatus && loadedTemplateStatus !== "draft");

  const updateDraft = (updates: Partial<TemplateDraft> | ((current: TemplateDraft) => Partial<TemplateDraft>)) => {
    const currentBase = draftOverride?.identity === activeTemplateIdentity
      ? draftOverride.value
      : sourceDraft;
    const nextValue = typeof updates === "function"
      ? { ...currentBase, ...updates(currentBase) }
      : { ...currentBase, ...updates };

    setDraftOverride({
      identity: activeTemplateIdentity,
      value: nextValue,
    });

    if (typeof updates === "function") {
      setFieldErrors({});
    } else {
      const changedFields = new Set(Object.keys(updates));
      setFieldErrors((current) => Object.fromEntries(
        Object.entries(current).filter(([field]) => !changedFields.has(field)),
      ));
    }
  };

  const validateWith = (schema: typeof templateDraftSchema | typeof templateContentSchema | typeof templateSettingsSchema) => {
    const result = schema.safeParse(effectiveDraft);
    const errors = getTemplateFieldErrors(result);
    setFieldErrors(errors);
    return result.success;
  };

  const validateCurrentStep = () => {
    if (step === 1) return validateWith(templateContentSchema);
    if (step === 2) return validateWith(templateSettingsSchema);
    if (step >= 3) return validateWith(templateDraftSchema);
    return true;
  };

  const isDraftValid = templateDraftSchema.safeParse(effectiveDraft).success;

  const toPayload = (): TemplatePayload => ({
    name: effectiveDraft.name.trim(),
    subject: effectiveDraft.subject.trim(),
    body_html: effectiveDraft.body_html,
    description: effectiveDraft.description.trim() || null,
    preheader: effectiveDraft.preheader.trim() || null,
    from_name: effectiveDraft.from_name.trim() || null,
    from_email: effectiveDraft.from_email.trim() || null,
    category_id: effectiveDraft.category_id,
    tags: effectiveDraft.tags,
    is_default: effectiveDraft.is_default,
    smart_personalization_enabled: false,
  });

  const applyServerFieldErrors = (error: unknown) => {
    const raw = getApiFieldErrors(error);
    const allowedFields = new Set([
      "name", "subject", "body_html", "description", "preheader",
      "from_name", "from_email", "category_id", "tags", "is_default",
    ]);
    const next: TemplateFieldErrors = {};
    for (const [path, message] of Object.entries(raw)) {
      const field = path.split(".").filter(Boolean).at(-1) ?? path;
      if (allowedFields.has(field) && !next[field]) next[field] = message;
    }
    if (Object.keys(next).length === 0) return false;
    setFieldErrors(next);
    const contentFields = new Set(["name", "subject", "body_html", "preheader"]);
    setStep(Object.keys(next).some((field) => contentFields.has(field)) ? 1 : 2);
    setFeedback(null);
    return true;
  };

  const saveTemplate = async (): Promise<EmailTemplate | null> => {
    if (!validateWith(templateDraftSchema)) {
      const contentResult = templateContentSchema.safeParse(effectiveDraft);
      setStep(contentResult.success ? 2 : 1);
      setFeedback(null);
      return null;
    }

    setFeedback(null);
    try {
      if (persistedTemplateUuid) {
        const updated = (await updateMutation.mutateAsync({
          uuid: persistedTemplateUuid,
          payload: toPayload(),
        })) as EmailTemplate;
        setFeedback({ tone: "success", text: "Template draft saved successfully." });
        return updated;
      }

      const created = (await createMutation.mutateAsync(toPayload())) as EmailTemplate;
      setCreatedTemplateUuid(created.uuid);
      setFeedback({ tone: "success", text: "Template draft created successfully." });
      return created;
    } catch (error) {
      if (!applyServerFieldErrors(error)) {
        setFeedback({ tone: "error", text: getApiErrorMessage(error, "Template could not be saved.") });
      }
      return null;
    }
  };

  const ensureTemplateForAssets = async (): Promise<string | null> => {
    if (persistedTemplateUuid) return persistedTemplateUuid;
    if (!validateWith(templateContentSchema)) {
      setStep(1);
      return null;
    }
    try {
      const created = (await createMutation.mutateAsync(toPayload())) as EmailTemplate;
      setCreatedTemplateUuid(created.uuid);
      return created.uuid;
    } catch (error) {
      if (!applyServerFieldErrors(error)) {
        setFeedback({ tone: "error", text: getApiErrorMessage(error, "A draft could not be created for the image upload.") });
      }
      return null;
    }
  };

  const saveDraft = async () => {
    const saved = await saveTemplate();
    if (!saved) return;
    allowNavigationRef.current = true;
    showToast("Template draft saved successfully.", "success");
    navigate({ to: "/templates" });
  };

  const publish = async () => {
    if (step !== steps.length - 1 || !validateWith(templateDraftSchema)) return;
    const saved = await saveTemplate();
    if (!saved) return;
    try {
      await publishMutation.mutateAsync(saved.uuid);
      allowNavigationRef.current = true;
      showToast("Template published successfully.", "success");
      navigate({ to: "/templates" });
    } catch (error) {
      setFeedback({ tone: "error", text: getApiErrorMessage(error, "Template was saved but could not be published.") });
    }
  };

  const next = () => {
    if (!validateCurrentStep()) {
      setFeedback(null);
      return;
    }
    setFeedback(null);
    setStep((current) => Math.min(steps.length - 1, current + 1));
  };

  const previous = () => {
    setFeedback(null);
    setStep((current) => Math.max(editing ? 1 : 0, current - 1));
  };

  if (editing && templateQuery.isLoading) {
    return (
      <PageContainer className="space-y-4">
        <div className="h-10 w-72 animate-pulse rounded-xl bg-[#EEE9DC]" />
        <div className="h-[620px] animate-pulse rounded-2xl bg-[#F1EDE3]" />
      </PageContainer>
    );
  }

  if (editing && templateQuery.isError) {
    return (
      <PageContainer>
        <InlineNotice tone="error">
          {getApiErrorMessage(templateQuery.error, "The template could not be opened.")}
        </InlineNotice>
      </PageContainer>
    );
  }

  if (editing && editingLocked) {
    return (
      <PageContainer>
        <InlineNotice tone="error">
          Published and archived templates are read-only in this editor. Duplicate the template to create a new draft before editing.
        </InlineNotice>
        <div className="mt-4">
          <Link
            to="/templates/$templateUuid"
            params={{ templateUuid: templateUuid ?? "" }}
            className="inline-flex items-center gap-2 rounded-xl border border-[#DED7C7] bg-white px-4 py-2.5 text-sm font-semibold text-[#5E5230]"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Template
          </Link>
        </div>
      </PageContainer>
    );
  }

  const saveBlockedNavigationAsDraft = async () => {
    const saved = await saveTemplate();
    if (!saved || blocker.status !== "blocked") return;
    allowNavigationRef.current = true;
    showToast("Template draft saved successfully.", "success");
    blocker.proceed();
  };

  const leaveBlockedNavigation = () => {
    if (blocker.status !== "blocked") return;
    allowNavigationRef.current = true;
    blocker.proceed();
  };

  return (
    <PageContainer>
      <ConfirmDialog
        open={blocker.status === "blocked"}
        onOpenChange={(open) => { if (!open && blocker.status === "blocked") blocker.reset(); }}
        title="Save your template before leaving?"
        description="You have unsaved template changes. Save them as a draft, leave without saving, or cancel to keep editing."
        confirmLabel="Save as Draft"
        secondaryLabel="Leave Without Saving"
        cancelLabel="Cancel"
        variant="warning"
        isLoading={createMutation.isPending || updateMutation.isPending}
        onConfirm={saveBlockedNavigationAsDraft}
        onSecondary={leaveBlockedNavigation}
      />
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <Link to="/templates" className="inline-flex items-center gap-2 text-sm font-medium text-[#7A6208] hover:underline">
            <ArrowLeft className="h-4 w-4" /> Back to Templates
          </Link>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-[#111827]">
            {editing ? "Edit Template" : "Create Template"}
          </h1>
          <p className="mt-1.5 text-sm text-[#756E5C]">
            Build and save a reusable email template using the approved Phase 1 flow.
          </p>
        </div>
        <button
          type="button"
          onClick={publish}
          disabled={step !== steps.length - 1 || !isDraftValid || publishMutation.isPending || createMutation.isPending || updateMutation.isPending}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#D9CFB8] bg-white px-4 py-2.5 text-sm font-semibold text-[#5E5230] hover:bg-[#FCF8EC] disabled:opacity-55"
        >
          <Send className="h-4 w-4" /> {publishMutation.isPending ? "Publishing..." : "Publish"}
        </button>
      </div>

      <div className="mt-7 overflow-x-auto pb-2">
        <div className="flex min-w-[620px] items-center">
          {steps.map((label, index) => {
            const disabled = editing && index === 0;
            const completed = index < step;
            const active = index === step;
            return (
              <div key={label} className="flex flex-1 items-center last:flex-none">
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => !disabled && index <= step && setStep(index)}
                  className="flex items-center gap-2 text-xs font-semibold"
                >
                  <span
                    className={`flex h-8 w-8 items-center justify-center rounded-full border ${
                      completed
                        ? "border-[#8F740D] bg-[#8F740D] text-white"
                        : active
                          ? "border-[#8F740D] bg-[#F8F0D7] text-[#7A6208]"
                          : "border-[#DAD4C7] bg-white text-[#8D8676]"
                    }`}
                  >
                    {completed ? <Check className="h-4 w-4" /> : index + 1}
                  </span>
                  <span className={active ? "text-[#7A6208]" : "text-[#746D5C]"}>{label}</span>
                </button>
                {index < steps.length - 1 && <div className="mx-4 h-px flex-1 bg-[#DED8CA]" />}
              </div>
            );
          })}
        </div>
      </div>

      {feedback && (
        <div className="mt-5">
          <InlineNotice tone={feedback.tone}>{feedback.text}</InlineNotice>
        </div>
      )}

      <section className="mt-5 min-w-0 overflow-hidden rounded-2xl border border-[#E8E1D0] bg-white p-4 shadow-[0_10px_30px_rgba(66,54,16,0.04)] sm:p-6">
        {step === 0 && (
          <TemplateGalleryStep
            onBlank={() => setStep(1)}
            onCopied={(template) =>
              navigate({ to: "/templates/$templateUuid/edit", params: { templateUuid: template.uuid } })
            }
          />
        )}
        {step === 1 && (
          <TemplateContentStep
            draft={effectiveDraft}
            updateDraft={updateDraft}
            templateUuid={persistedTemplateUuid}
            resolveTemplateUuid={ensureTemplateForAssets}
            errors={fieldErrors}
          />
        )}
        {step === 2 && <TemplateSettingsStep draft={effectiveDraft} updateDraft={updateDraft} errors={fieldErrors} />}
        {step === 3 && <TemplatePreviewStep draft={effectiveDraft} />}
        {step === 4 && <TemplateReviewStep draft={effectiveDraft} categoryName={categoryName} />}
      </section>

      {step > 0 && (
        <div className="mt-5 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
          <button
            type="button"
            onClick={previous}
            disabled={editing && step === 1}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#D9CFB8] bg-white px-4 py-3 text-sm font-semibold text-[#5E5230] disabled:opacity-40"
          >
            <ArrowLeft className="h-4 w-4" /> Back
          </button>
          {step < steps.length - 1 ? (
            <button
              type="button"
              onClick={next}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-5 py-3 text-sm font-semibold text-white shadow-button hover:bg-[#735D0B]"
            >
              Continue <ArrowRight className="h-4 w-4" />
            </button>
          ) : (
            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={saveDraft}
                disabled={createMutation.isPending || updateMutation.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#D0C39B] bg-white px-5 py-3 text-sm font-semibold text-[#6F5A0B]"
              >
                <Save className="h-4 w-4" /> {createMutation.isPending || updateMutation.isPending ? "Saving…" : "Save Draft"}
              </button>
              <button
                type="button"
                onClick={publish}
                disabled={!isDraftValid || publishMutation.isPending || createMutation.isPending || updateMutation.isPending}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-5 py-3 text-sm font-semibold text-white shadow-button disabled:opacity-55"
              >
                <Send className="h-4 w-4" /> {publishMutation.isPending ? "Publishing..." : "Save & Publish"}
              </button>
            </div>
          )}
        </div>
      )}
    </PageContainer>
  );
};
