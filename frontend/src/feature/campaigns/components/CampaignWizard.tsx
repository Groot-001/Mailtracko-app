import { useCallback, useMemo, useRef, useState } from "react";
import { Link, useBlocker, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, ArrowRight, Check, Rocket, Save } from "lucide-react";
import { InlineNotice } from "../../../shared/components/InlineNotice";
import { ConfirmDialog } from "../../../shared/components/ConfirmDialog";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { zonedLocalDateTimeToIso } from "../../../shared/utils/dateTime";
import {
  useABTest,
  useCampaign,
  useConfigureABTest,
  useConfigureSequence,
  useCreateCampaign,
  useLaunchCampaign,
  usePreviewSequence,
  useReviewCampaign,
  useScheduleCampaign,
  useSequence,
  useUpdateCampaign,
} from "../hooks/useCampaigns";
import type {
  ABVariantPayload,
  Campaign,
  CampaignGoal,
  CampaignPriority,
  CampaignReview,
  CampaignStep,
  CampaignType,
  ConfigureABTestPayload,
  ConfigureSequencePayload,
  SequencePreview,
  SequenceStepPayload,
} from "../types/campaign.types";
import { CampaignAudienceStep } from "./CampaignAudienceStep";
import { CampaignContentStep } from "./CampaignContentStep";
import { CampaignReviewStep } from "./CampaignReviewStep";
import { CampaignScheduleStep } from "./CampaignScheduleStep";
import { CampaignSenderStep } from "./CampaignSenderStep";
import { CampaignSetupStep } from "./CampaignSetupStep";

export interface CampaignDraft {
  name: string;
  description: string;
  campaign_type: CampaignType;
  goal: CampaignGoal;
  priority: CampaignPriority;
  contact_list_uuid: string;
  email_account_uuid: string;
  template_uuid: string;
  timezone: string;
  daily_limit: number | null;
  batch_size: number;
  delivery_mode: "immediate" | "scheduled";
  scheduled_at_local: string;
  sequence_steps: SequenceStepPayload[];
  ab_test_percentage: number;
  ab_winner_metric: ConfigureABTestPayload["winner_metric"];
  ab_auto_select_winner: boolean;
  ab_variants: [ABVariantPayload, ABVariantPayload];
}

interface CampaignWizardProps {
  campaignUuid?: string;
}

const workflowSteps: Array<{ key: CampaignStep; label: string }> = [
  { key: "setup", label: "Setup" },
  { key: "audience", label: "Audience" },
  { key: "sender", label: "Sender" },
  { key: "content", label: "Content" },
  { key: "schedule", label: "Schedule" },
  { key: "review", label: "Review" },
];

const browserTimezone = () => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
};

const defaultEmailStep = (): SequenceStepPayload => ({
  step_order: 1,
  step_type: "email",
  template_uuid: "",
  subject_override: null,
  body_html_override: null,
  is_enabled: true,
});

const blankCampaign: CampaignDraft = {
  name: "",
  description: "",
  campaign_type: "regular",
  goal: "outreach",
  priority: "normal",
  contact_list_uuid: "",
  email_account_uuid: "",
  template_uuid: "",
  timezone: browserTimezone(),
  daily_limit: null,
  batch_size: 25,
  delivery_mode: "immediate",
  scheduled_at_local: "",
  sequence_steps: [defaultEmailStep()],
  ab_test_percentage: 100,
  ab_winner_metric: "reply_rate",
  ab_auto_select_winner: false,
  ab_variants: [
    {
      variant_type: "a",
      name: "Variant A",
      template_uuid: "",
      subject_override: null,
      body_html_override: null,
      allocation_percentage: 50,
    },
    {
      variant_type: "b",
      name: "Variant B",
      template_uuid: "",
      subject_override: null,
      body_html_override: null,
      allocation_percentage: 50,
    },
  ],
};

const toLocalDateTime = (value: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 16);
};

const stepIndexFor = (step: string) => {
  const index = workflowSteps.findIndex((item) => item.key === step);
  return index >= 0 ? index : 0;
};

type DraftPatch = Partial<CampaignDraft>;

const mergeDraftPatch = (sourceDraft: CampaignDraft, patch?: DraftPatch): CampaignDraft => {
  if (!patch || Object.keys(patch).length === 0) {
    return sourceDraft;
  }

  const merged: CampaignDraft = { ...sourceDraft };
  if (patch.name !== undefined) merged.name = patch.name;
  if (patch.description !== undefined) merged.description = patch.description;
  if (patch.campaign_type !== undefined) merged.campaign_type = patch.campaign_type;
  if (patch.goal !== undefined) merged.goal = patch.goal;
  if (patch.priority !== undefined) merged.priority = patch.priority;
  if (patch.contact_list_uuid !== undefined) merged.contact_list_uuid = patch.contact_list_uuid;
  if (patch.email_account_uuid !== undefined) merged.email_account_uuid = patch.email_account_uuid;
  if (patch.template_uuid !== undefined) merged.template_uuid = patch.template_uuid;
  if (patch.timezone !== undefined) merged.timezone = patch.timezone;
  if (patch.daily_limit !== undefined) merged.daily_limit = patch.daily_limit;
  if (patch.batch_size !== undefined) merged.batch_size = patch.batch_size;
  if (patch.delivery_mode !== undefined) merged.delivery_mode = patch.delivery_mode;
  if (patch.scheduled_at_local !== undefined) merged.scheduled_at_local = patch.scheduled_at_local;
  if (patch.sequence_steps !== undefined) merged.sequence_steps = patch.sequence_steps;
  if (patch.ab_test_percentage !== undefined) merged.ab_test_percentage = patch.ab_test_percentage;
  if (patch.ab_winner_metric !== undefined) merged.ab_winner_metric = patch.ab_winner_metric;
  if (patch.ab_auto_select_winner !== undefined) merged.ab_auto_select_winner = patch.ab_auto_select_winner;
  if (patch.ab_variants !== undefined) merged.ab_variants = patch.ab_variants;

  return merged;
};

const buildDraftPatch = (sourceDraft: CampaignDraft, nextDraft: CampaignDraft): DraftPatch => {
  const patch: DraftPatch = {};

  if (nextDraft.name !== sourceDraft.name) patch.name = nextDraft.name;
  if (nextDraft.description !== sourceDraft.description) patch.description = nextDraft.description;
  if (nextDraft.campaign_type !== sourceDraft.campaign_type) patch.campaign_type = nextDraft.campaign_type;
  if (nextDraft.goal !== sourceDraft.goal) patch.goal = nextDraft.goal;
  if (nextDraft.priority !== sourceDraft.priority) patch.priority = nextDraft.priority;
  if (nextDraft.contact_list_uuid !== sourceDraft.contact_list_uuid) patch.contact_list_uuid = nextDraft.contact_list_uuid;
  if (nextDraft.email_account_uuid !== sourceDraft.email_account_uuid) patch.email_account_uuid = nextDraft.email_account_uuid;
  if (nextDraft.template_uuid !== sourceDraft.template_uuid) patch.template_uuid = nextDraft.template_uuid;
  if (nextDraft.timezone !== sourceDraft.timezone) patch.timezone = nextDraft.timezone;
  if (nextDraft.daily_limit !== sourceDraft.daily_limit) patch.daily_limit = nextDraft.daily_limit;
  if (nextDraft.batch_size !== sourceDraft.batch_size) patch.batch_size = nextDraft.batch_size;
  if (nextDraft.delivery_mode !== sourceDraft.delivery_mode) patch.delivery_mode = nextDraft.delivery_mode;
  if (nextDraft.scheduled_at_local !== sourceDraft.scheduled_at_local) patch.scheduled_at_local = nextDraft.scheduled_at_local;
  if (nextDraft.sequence_steps !== sourceDraft.sequence_steps) patch.sequence_steps = nextDraft.sequence_steps;
  if (nextDraft.ab_test_percentage !== sourceDraft.ab_test_percentage) patch.ab_test_percentage = nextDraft.ab_test_percentage;
  if (nextDraft.ab_winner_metric !== sourceDraft.ab_winner_metric) patch.ab_winner_metric = nextDraft.ab_winner_metric;
  if (nextDraft.ab_auto_select_winner !== sourceDraft.ab_auto_select_winner) patch.ab_auto_select_winner = nextDraft.ab_auto_select_winner;
  if (nextDraft.ab_variants !== sourceDraft.ab_variants) patch.ab_variants = nextDraft.ab_variants;

  return patch;
};

const campaignToDraft = (campaign: Campaign): CampaignDraft => ({
  ...blankCampaign,
  name: campaign.name,
  description: campaign.description ?? "",
  campaign_type: campaign.campaign_type as CampaignType,
  goal: campaign.goal as CampaignGoal,
  priority: campaign.priority as CampaignPriority,
  contact_list_uuid: campaign.contact_list_uuid ?? "",
  email_account_uuid: campaign.email_account_uuid ?? "",
  template_uuid: campaign.template_uuid ?? "",
  timezone: campaign.timezone || browserTimezone(),
  daily_limit: campaign.daily_limit,
  batch_size: campaign.batch_size || 25,
  delivery_mode: campaign.scheduled_at ? "scheduled" : "immediate",
  scheduled_at_local: toLocalDateTime(campaign.scheduled_at),
});

const hasHtmlText = (value?: string | null) =>
  Boolean(value?.replace(/<[^>]*>/g, " ").replace(/&nbsp;/g, " ").trim());

export const CampaignWizard = ({ campaignUuid }: CampaignWizardProps) => {
  const editing = Boolean(campaignUuid);
  const navigate = useNavigate();
  const allowNavigationRef = useRef(false);
  const campaignQuery = useCampaign(campaignUuid ?? "");
  const sequenceQuery = useSequence(
    campaignUuid ?? "",
    editing && campaignQuery.data?.campaign_type === "sequence",
  );
  const abTestQuery = useABTest(
    campaignUuid ?? "",
    editing && campaignQuery.data?.campaign_type === "ab_test",
  );
  const createMutation = useCreateCampaign();
  const updateMutation = useUpdateCampaign();
  const configureSequenceMutation = useConfigureSequence();
  const configureABMutation = useConfigureABTest();
  const reviewMutation = useReviewCampaign();
  const scheduleMutation = useScheduleCampaign();
  const launchMutation = useLaunchCampaign();
  const previewSequenceMutation = usePreviewSequence();

  const [draftOverride, setDraftOverride] = useState<{
    identity: string;
    patch: DraftPatch;
  } | null>(null);
  const [stepOverride, setStepOverride] = useState<{
    identity: string;
    value: number;
  } | null>(null);
  const [workingUuid, setWorkingUuid] = useState(campaignUuid ?? "");
  const [review, setReview] = useState<CampaignReview | null>(null);
  const [sequencePreview, setSequencePreview] = useState<SequencePreview | null>(null);
  const [feedback, setFeedback] = useState<{
    tone: "success" | "error" | "info";
    text: string;
  } | null>(null);
  const [activeSaveAction, setActiveSaveAction] = useState<"draft" | "continue" | null>(null);

  const editorIdentity = campaignUuid ?? "create";
  const sourceDraft = useMemo<CampaignDraft>(() => {
    const baseDraft = campaignQuery.data
      ? campaignToDraft(campaignQuery.data)
      : blankCampaign;

    const sequenceDraft = sequenceQuery.data
      ? {
          ...baseDraft,
          sequence_steps: sequenceQuery.data.steps.map((step, index) => ({
            step_order: index + 1,
            step_type: step.step_type,
            template_uuid: step.template_uuid ?? "",
            subject_override: step.subject_override ?? null,
            body_html_override: step.body_html_override ?? null,
            delay_value: step.delay_value ?? null,
            delay_unit: step.delay_unit ?? null,
            is_enabled: step.is_enabled,
          })),
        }
      : baseDraft;

    const abDraft = abTestQuery.data && abTestQuery.data.variants.length === 2
      ? (() => {
          const abVariants: [ABVariantPayload, ABVariantPayload] = [
            {
              variant_type: "a",
              name: abTestQuery.data.variants[0].name,
              template_uuid: abTestQuery.data.variants[0].template_uuid ?? "",
              subject_override: abTestQuery.data.variants[0].subject_override ?? null,
              body_html_override: abTestQuery.data.variants[0].body_html_override ?? null,
              allocation_percentage: abTestQuery.data.variants[0].allocation_percentage,
            },
            {
              variant_type: "b",
              name: abTestQuery.data.variants[1].name,
              template_uuid: abTestQuery.data.variants[1].template_uuid ?? "",
              subject_override: abTestQuery.data.variants[1].subject_override ?? null,
              body_html_override: abTestQuery.data.variants[1].body_html_override ?? null,
              allocation_percentage: abTestQuery.data.variants[1].allocation_percentage,
            },
          ];
          const abWinnerMetric = abTestQuery.data.winner_metric as CampaignDraft["ab_winner_metric"];

          return {
            ...sequenceDraft,
            ab_test_percentage: abTestQuery.data.test_percentage,
            ab_winner_metric: abWinnerMetric,
            ab_auto_select_winner: abTestQuery.data.auto_select_winner,
            ab_variants: abVariants,
          } satisfies CampaignDraft;
        })()
      : sequenceDraft;

    return abDraft;
  }, [abTestQuery.data, campaignQuery.data, sequenceQuery.data]);

  const effectiveDraft = useMemo<CampaignDraft>(() => {
    if (draftOverride?.identity === editorIdentity) {
      return mergeDraftPatch(sourceDraft, draftOverride.patch);
    }

    return sourceDraft;
  }, [draftOverride, editorIdentity, sourceDraft]);

  const isDirty = Boolean(
    draftOverride?.identity === editorIdentity &&
    Object.keys(draftOverride.patch).length > 0,
  );

  const blocker = useBlocker({
    shouldBlockFn: () => isDirty && !allowNavigationRef.current,
    enableBeforeUnload: () => isDirty && !allowNavigationRef.current,
    withResolver: true,
  });

  const sourceStepIndex = useMemo(() => {
    if (!campaignQuery.data) return 0;
    return Math.min(workflowSteps.length - 1, stepIndexFor(campaignQuery.data.current_step));
  }, [campaignQuery.data]);

  const effectiveStepIndex = stepOverride?.identity === editorIdentity
    ? stepOverride.value
    : sourceStepIndex;

  const currentStep = workflowSteps[effectiveStepIndex];
  const updateDraft = useCallback((updates: Partial<CampaignDraft> | ((current: CampaignDraft) => Partial<CampaignDraft>)) => {
    const currentBase: CampaignDraft = effectiveDraft;
    const resolvedUpdates: Partial<CampaignDraft> = typeof updates === "function"
      ? updates(currentBase)
      : updates;
    const nextValue: CampaignDraft = {
      ...currentBase,
      ...resolvedUpdates,
    };

    const nextPatch = buildDraftPatch(sourceDraft, nextValue);
    if (Object.keys(nextPatch).length > 0) {
      setDraftOverride({
        identity: editorIdentity,
        patch: nextPatch,
      });
      return;
    }

    setDraftOverride(null);
  }, [effectiveDraft, editorIdentity, sourceDraft]);

  const validateCurrentStep = () => {
    if (currentStep.key === "setup") {
      if (!effectiveDraft.name.trim()) return "Campaign name is required.";
    }
    if (currentStep.key === "audience" && !effectiveDraft.contact_list_uuid) {
      return "Select a collection before continuing.";
    }
    if (currentStep.key === "sender" && !effectiveDraft.email_account_uuid) {
      return "Select a sender account before continuing.";
    }
    if (currentStep.key === "content") {
      if (effectiveDraft.campaign_type === "regular" && !effectiveDraft.template_uuid) {
        return "Select a published template for this campaign.";
      }
      if (effectiveDraft.campaign_type === "sequence") {
        if (!effectiveDraft.sequence_steps.some((step) => step.step_type === "email")) {
          return "A sequence requires at least one email step.";
        }
        for (const step of effectiveDraft.sequence_steps) {
          if (step.step_type === "email") {
            const hasTemplate = Boolean(step.template_uuid);
            const hasOverride = Boolean(step.subject_override?.trim() && hasHtmlText(step.body_html_override));
            if (!hasTemplate && !hasOverride) {
              return `Email step ${step.step_order} requires a template or subject/body override.`;
            }
          }
          if (
            step.step_type === "delay" &&
            (!step.delay_value || step.delay_value < 1 || !step.delay_unit)
          ) {
            return `Delay step ${step.step_order} requires a valid delay and unit.`;
          }
        }
      }
      if (effectiveDraft.campaign_type === "ab_test") {
        if (effectiveDraft.ab_variants[0].allocation_percentage + effectiveDraft.ab_variants[1].allocation_percentage !== 100) {
          return "A/B allocation must total 100%.";
        }
        for (const variant of effectiveDraft.ab_variants) {
          const hasTemplate = Boolean(variant.template_uuid);
          const hasOverride = Boolean(variant.subject_override?.trim() && hasHtmlText(variant.body_html_override));
          if (!variant.name.trim()) return `Variant ${variant.variant_type.toUpperCase()} needs a name.`;
          if (!hasTemplate && !hasOverride) {
            return `Variant ${variant.variant_type.toUpperCase()} requires a template or subject/body override.`;
          }
        }
      }
    }
    if (currentStep.key === "schedule" && effectiveDraft.delivery_mode === "scheduled") {
      if (!effectiveDraft.scheduled_at_local) return "Choose a future date and time.";
      const scheduledAt = zonedLocalDateTimeToIso(
        effectiveDraft.scheduled_at_local,
        effectiveDraft.timezone,
      );
      if (!scheduledAt || new Date(scheduledAt).getTime() <= Date.now()) {
        return "Scheduled date and time must be valid and in the future.";
      }
    }
    return null;
  };

  const createPayload = () => ({
    name: effectiveDraft.name.trim(),
    description: effectiveDraft.description.trim() || null,
    campaign_type: effectiveDraft.campaign_type,
    goal: effectiveDraft.goal,
    priority: effectiveDraft.priority,
    timezone: effectiveDraft.timezone,
    email_account_uuid: effectiveDraft.email_account_uuid || null,
    template_uuid: effectiveDraft.campaign_type === "regular" ? effectiveDraft.template_uuid || null : null,
    contact_list_uuid: effectiveDraft.contact_list_uuid || null,
    daily_limit: effectiveDraft.daily_limit,
    batch_size: effectiveDraft.batch_size,
  });

  const updatePayload = (nextStep?: CampaignStep) => ({
    name: effectiveDraft.name.trim(),
    description: effectiveDraft.description.trim() || null,
    goal: effectiveDraft.goal,
    priority: effectiveDraft.priority,
    current_step: nextStep,
    timezone: effectiveDraft.timezone,
    email_account_uuid: effectiveDraft.email_account_uuid || null,
    template_uuid: effectiveDraft.campaign_type === "regular" ? effectiveDraft.template_uuid || null : null,
    contact_list_uuid: effectiveDraft.contact_list_uuid || null,
    daily_limit: effectiveDraft.daily_limit,
    batch_size: effectiveDraft.batch_size,
  });

  const persistCampaign = async (nextStep?: CampaignStep): Promise<Campaign> => {
    if (workingUuid) {
      return (await updateMutation.mutateAsync({
        uuid: workingUuid,
        payload: updatePayload(nextStep),
      })) as Campaign;
    }

    const created = (await createMutation.mutateAsync(createPayload())) as Campaign;
    setWorkingUuid(created.uuid);
    if (!nextStep || nextStep === "setup") return created;
    return (await updateMutation.mutateAsync({
      uuid: created.uuid,
      payload: { current_step: nextStep },
    })) as Campaign;
  };

  const persistContentConfiguration = async (uuid: string) => {
    if (effectiveDraft.campaign_type === "sequence") {
      const payload: ConfigureSequencePayload = {
        stop_on_reply: true,
        stop_on_unsubscribe: true,
        // Send the stop-condition defaults explicitly
        // while keeping the approved Phase 1 sequence UI unchanged.
        stop_on_click: false,
        stop_on_meeting: false,
        custom_stop_events: [],
        steps: effectiveDraft.sequence_steps.map((step, index) => ({
          ...step,
          step_order: index + 1,
          template_uuid: step.template_uuid || null,
          subject_override: step.subject_override?.trim() || null,
          body_html_override: step.body_html_override || null,
          delay_value: step.step_type === "delay" ? step.delay_value : null,
          delay_unit: step.step_type === "delay" ? step.delay_unit : null,
        })),
      };
      await configureSequenceMutation.mutateAsync({ uuid, payload });
    }

    if (effectiveDraft.campaign_type === "ab_test") {
      const payload: ConfigureABTestPayload = {
        test_percentage: effectiveDraft.ab_test_percentage,
        winner_metric: effectiveDraft.ab_winner_metric,
        auto_select_winner: effectiveDraft.ab_auto_select_winner,
        // Use the service defaults for settings outside the basic workflow.
        minimum_sample_size: 0,
        test_duration_hours: null,
        variants: effectiveDraft.ab_variants.map((variant) => ({
          ...variant,
          name: variant.name.trim(),
          template_uuid: variant.template_uuid || null,
          subject_override: variant.subject_override?.trim() || null,
          body_html_override: variant.body_html_override || null,
        })) as [ABVariantPayload, ABVariantPayload],
      };
      await configureABMutation.mutateAsync({ uuid, payload });
    }
  };

  const saveDraft = async () => {
    setFeedback(null);
    if (!effectiveDraft.name.trim()) {
      setFeedback({ tone: "error", text: "Campaign name is required before saving a draft." });
      return;
    }
    setActiveSaveAction("draft");
    try {
      const saved = await persistCampaign(currentStep.key);
      if (currentStep.key === "content") await persistContentConfiguration(saved.uuid);
      setFeedback({ tone: "success", text: "Campaign draft saved successfully." });
      setDraftOverride(null);
      if (!editing) {
        allowNavigationRef.current = true;
        navigate({
          to: "/campaigns/$campaignUuid/edit",
          params: { campaignUuid: saved.uuid },
        });
      }
    } catch (error) {
      setFeedback({
        tone: "error",
        text: getApiErrorMessage(error, "Campaign draft could not be saved."),
      });
    } finally {
      setActiveSaveAction(null);
    }
  };

  const saveBlockedNavigationAsDraft = async () => {
    if (blocker.status !== "blocked") return;
    if (!effectiveDraft.name.trim()) {
      setFeedback({ tone: "error", text: "Campaign name is required before saving a draft." });
      return;
    }
    setActiveSaveAction("draft");
    try {
      const saved = await persistCampaign(currentStep.key);
      if (currentStep.key === "content") await persistContentConfiguration(saved.uuid);
      setDraftOverride(null);
      allowNavigationRef.current = true;
      blocker.proceed();
    } catch (error) {
      setFeedback({ tone: "error", text: getApiErrorMessage(error, "Campaign draft could not be saved.") });
    } finally {
      setActiveSaveAction(null);
    }
  };

  const leaveBlockedNavigation = () => {
    if (blocker.status !== "blocked") return;
    allowNavigationRef.current = true;
    blocker.proceed();
  };

  const runReview = async (uuid: string) => {
    setReview(null);
    setSequencePreview(null);
    const result = await reviewMutation.mutateAsync(uuid);
    setReview(result);

    if (effectiveDraft.campaign_type === "sequence") {
      try {
        const startsAt =
          effectiveDraft.delivery_mode === "scheduled"
            ? zonedLocalDateTimeToIso(effectiveDraft.scheduled_at_local, effectiveDraft.timezone)
            : null;
        const preview = await previewSequenceMutation.mutateAsync({ uuid, startsAt });
        setSequencePreview(preview);
      } catch {
        // Integration note: readiness remains authoritative; preview failure does not alter campaign state.
        setSequencePreview(null);
      }
    }

    return result;
  };

  const next = async () => {
    const validationError = validateCurrentStep();
    if (validationError) {
      setFeedback({ tone: "error", text: validationError });
      return;
    }

    const nextIndex = Math.min(workflowSteps.length - 1, effectiveStepIndex + 1);
    const nextStep = workflowSteps[nextIndex].key;
    setFeedback(null);
    setActiveSaveAction("continue");

    try {
      const saved = await persistCampaign(nextStep);
      if (currentStep.key === "content") await persistContentConfiguration(saved.uuid);
      if (nextStep === "review") await runReview(saved.uuid);

      if (!editing && effectiveStepIndex === 0) {
        allowNavigationRef.current = true;
        navigate({
          to: "/campaigns/$campaignUuid/edit",
          params: { campaignUuid: saved.uuid },
        });
        return;
      }
      setStepOverride({ identity: editorIdentity, value: nextIndex });
    } catch (error) {
      setFeedback({
        tone: "error",
        text: getApiErrorMessage(error, "Campaign step could not be saved."),
      });
    } finally {
      setActiveSaveAction(null);
    }
  };

  const previous = () => {
    setFeedback(null);
    setStepOverride((current) => ({
      identity: editorIdentity,
      value: Math.max(0, (current?.identity === editorIdentity ? current.value : effectiveStepIndex) - 1),
    }));
  };

  const finalizeCampaign = async () => {
    if (!workingUuid) return;
    setFeedback(null);
    try {
      await persistCampaign("review");
      const result = await runReview(workingUuid);
      if (!result.ready) {
        setFeedback({ tone: "error", text: "Resolve the backend review errors before launch." });
        return;
      }

      if (effectiveDraft.delivery_mode === "scheduled") {
        const scheduledAt = zonedLocalDateTimeToIso(
          effectiveDraft.scheduled_at_local,
          effectiveDraft.timezone,
        );
        if (!scheduledAt) {
          setFeedback({ tone: "error", text: "The selected schedule could not be converted." });
          return;
        }
        await scheduleMutation.mutateAsync({
          uuid: workingUuid,
          scheduledAt,
          timezone: effectiveDraft.timezone,
        });
      } else {
        await launchMutation.mutateAsync(workingUuid);
      }

      allowNavigationRef.current = true;
      navigate({
        to: "/campaigns/$campaignUuid",
        params: { campaignUuid: workingUuid },
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        text: getApiErrorMessage(error, "Campaign could not be launched or scheduled."),
      });
    }
  };

  const pageBusy =
    createMutation.isPending ||
    updateMutation.isPending ||
    configureSequenceMutation.isPending ||
    configureABMutation.isPending ||
    scheduleMutation.isPending ||
    launchMutation.isPending;

  const isNonDraft = editing && campaignQuery.data && campaignQuery.data.status !== "draft";

  const content = useMemo(() => {
    if (currentStep.key === "setup") {
      return (
        <CampaignSetupStep
          draft={effectiveDraft}
          updateDraft={updateDraft}
          campaignTypeLocked={editing}
        />
      );
    }
    if (currentStep.key === "audience") {
      return <CampaignAudienceStep draft={effectiveDraft} updateDraft={updateDraft} />;
    }
    if (currentStep.key === "sender") {
      return <CampaignSenderStep draft={effectiveDraft} updateDraft={updateDraft} />;
    }
    if (currentStep.key === "content") {
      return <CampaignContentStep draft={effectiveDraft} updateDraft={updateDraft} />;
    }
    if (currentStep.key === "schedule") {
      return <CampaignScheduleStep draft={effectiveDraft} updateDraft={updateDraft} />;
    }
    return (
      <CampaignReviewStep
        draft={effectiveDraft}
        review={review}
        sequencePreview={sequencePreview}
        reviewing={reviewMutation.isPending || previewSequenceMutation.isPending}
      />
    );
  }, [currentStep.key, effectiveDraft, editing, review, reviewMutation.isPending, previewSequenceMutation.isPending, sequencePreview, updateDraft]);

  if (editing && campaignQuery.isLoading) {
    return (
      <div className="mx-auto max-w-[1480px] space-y-4 px-4 py-6 sm:px-6 lg:px-8">
        <div className="h-10 w-72 animate-pulse rounded-xl bg-[#EEE9DC]" />
        <div className="h-[620px] animate-pulse rounded-2xl bg-[#F1EDE3]" />
      </div>
    );
  }

  if (editing && (campaignQuery.isError || !campaignQuery.data)) {
    return (
      <div className="mx-auto max-w-[1480px] px-4 py-6 sm:px-6 lg:px-8">
        <InlineNotice tone="error">
          {getApiErrorMessage(campaignQuery.error, "The campaign could not be opened.")}
        </InlineNotice>
      </div>
    );
  }

  if (isNonDraft && campaignQuery.data) {
    return (
      <div className="mx-auto max-w-[1480px] px-4 py-6 sm:px-6 lg:px-8">
        <InlineNotice>
          This campaign is currently {campaignQuery.data.status}. Only draft campaigns can be edited.
          <Link
            to="/campaigns/$campaignUuid"
            params={{ campaignUuid: campaignQuery.data.uuid }}
            className="ml-1 font-semibold underline"
          >
            Open campaign details
          </Link>
          .
        </InlineNotice>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1480px] px-4 py-6 sm:px-6 lg:px-8">
      <ConfirmDialog
        open={blocker.status === "blocked"}
        onOpenChange={(open) => { if (!open && blocker.status === "blocked") blocker.reset(); }}
        title="Save this campaign as a draft?"
        description="You have unsaved campaign changes. Save them as a draft, leave without saving, or cancel to keep editing."
        confirmLabel="Save as Draft"
        secondaryLabel="Leave Without Saving"
        cancelLabel="Cancel"
        variant="warning"
        isLoading={activeSaveAction === "draft"}
        onConfirm={saveBlockedNavigationAsDraft}
        onSecondary={leaveBlockedNavigation}
      />
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <Link
            to="/campaigns"
            className="inline-flex items-center gap-2 text-sm font-medium text-[#7A6208] hover:underline"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Campaigns
          </Link>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-[#111827]">
            {editing ? "Edit Campaign" : "Create Campaign"}
          </h1>
          <p className="mt-1.5 text-sm text-[#756E5C]">
            Configure Phase 1 campaign features with Sequence and A/B Testing inside Content.
          </p>
        </div>
        <button
          type="button"
          onClick={saveDraft}
          disabled={pageBusy}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#D9CFB8] bg-white px-4 py-2.5 text-sm font-semibold text-[#5E5230] hover:bg-[#FCF8EC] disabled:opacity-55"
        >
          <Save className="h-4 w-4" /> {activeSaveAction === "draft" ? "Saving..." : "Save Draft"}
        </button>
      </div>

      <div className="mt-7 overflow-x-auto pb-2">
        <div className="flex min-w-[760px] items-center">
          {workflowSteps.map((item, index) => {
            const completed = index < effectiveStepIndex;
            const active = index === effectiveStepIndex;
            return (
              <div key={item.key} className="flex flex-1 items-center last:flex-none">
                <button
                  type="button"
                  onClick={() => index <= effectiveStepIndex && setStepOverride({ identity: editorIdentity, value: index })}
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
                  <span className={active ? "text-[#7A6208]" : "text-[#746D5C]"}>
                    {item.label}
                  </span>
                </button>
                {index < workflowSteps.length - 1 && (
                  <div className="mx-4 h-px flex-1 bg-[#DED8CA]" />
                )}
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

      <section className="mt-5">{content}</section>

      <div className="mt-6 flex flex-col-reverse gap-3 border-t border-[#E5DDCA] pt-5 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={previous}
          disabled={effectiveStepIndex === 0 || pageBusy}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#D9CFB8] bg-white px-4 py-2.5 text-sm font-semibold text-[#5E5230] disabled:opacity-40"
        >
          <ArrowLeft className="h-4 w-4" /> Previous
        </button>

        {currentStep.key === "review" ? (
          <button
            type="button"
            onClick={finalizeCampaign}
            disabled={pageBusy || reviewMutation.isPending || review?.ready === false}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-5 py-3 text-sm font-semibold text-white shadow-button hover:bg-[#735D0B] disabled:opacity-50"
          >
            <Rocket className="h-4 w-4" />
            {pageBusy
              ? "Processing..."
              : effectiveDraft.delivery_mode === "scheduled"
                ? "Schedule Campaign"
                : "Launch Campaign"}
          </button>
        ) : (
          <button
            type="button"
            onClick={next}
            disabled={pageBusy}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-5 py-3 text-sm font-semibold text-white shadow-button hover:bg-[#735D0B] disabled:opacity-50"
          >
            {activeSaveAction === "continue" ? "Saving..." : "Save & Continue"} <ArrowRight className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
};
