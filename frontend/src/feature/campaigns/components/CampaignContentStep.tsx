import { useEffect, useMemo } from "react";
import {
  ArrowDown,
  ArrowUp,
  Clock3,
  FlaskConical,
  Mail,
  Plus,
  Trash2,
} from "lucide-react";
import { AppSelect } from "../../../shared/components/AppSelect";
import { useTemplates } from "../../templates/hooks/useTemplates";
import { RichTextEditor } from "../../templates/components/RichTextEditor";
import type { ABVariantPayload, DelayUnit, SequenceStepPayload } from "../types/campaign.types";
import type { CampaignDraft } from "./CampaignWizard";

interface CampaignContentStepProps {
  draft: CampaignDraft;
  updateDraft: (updates: Partial<CampaignDraft>) => void;
}

const fieldClass =
  "h-11 w-full rounded-xl border border-[#DED7C7] bg-white px-3 text-sm outline-none focus:border-[#A88916] focus:ring-2 focus:ring-[#E9DFAE]";

const TemplateSelect = ({
  value,
  onChange,
  label = "Email Template",
}: {
  value: string;
  onChange: (value: string) => void;
  label?: string;
}) => {
  const templatesQuery = useTemplates({ status: "published", limit: 100, offset: 0 });
  const defaultTemplate = useMemo(
    () => templatesQuery.data?.items.find((t) => t.is_default),
    [templatesQuery.data?.items],
  );

  useEffect(() => {
    if (!value && defaultTemplate) {
      onChange(defaultTemplate.uuid);
    }
  }, [value, defaultTemplate, onChange]);

  return (
    <label className="block space-y-2">
      <span className="text-sm font-semibold text-[#302C24]">{label}</span>
      <AppSelect value={value} onValueChange={onChange} ariaLabel={label} searchable options={[{ value: "", label: "Select a published template" }, ...(templatesQuery.data?.items.map((template) => ({ value: template.uuid, label: `${template.name} — ${template.subject}` })) ?? [])]} />
      {templatesQuery.isError && (
        <span className="text-xs text-[#B42318]">Published templates could not be loaded.</span>
      )}
      {defaultTemplate && !value && (
        <span className="text-xs text-[#8F740D]">Default template selected automatically.</span>
      )}
    </label>
  );
};

const StandardContent = ({ draft, updateDraft }: CampaignContentStepProps) => (
  <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
    <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5 sm:p-6">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
          <Mail className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-[#171A22]">Campaign Content</h2>
          <p className="mt-1 text-sm text-[#756E5C]">
            Select the published template that will be sent by this campaign.
          </p>
        </div>
      </div>
      <div className="mt-6">
        <TemplateSelect
          value={draft.template_uuid}
          onChange={(template_uuid) => updateDraft({ template_uuid })}
        />
      </div>
    </section>

    <aside className="rounded-2xl border border-[#E8E1D0] bg-[#FFFCF3] p-5">
      <h3 className="font-semibold text-[#171A22]">Phase 1 Content</h3>
      <p className="mt-2 text-sm leading-6 text-[#756E5C]">
        The selected template remains reusable and is linked to the campaign by its UUID. Edit the
        template from the Templates module when its content needs to change.
      </p>
    </aside>
  </div>
);

const SequenceBuilder = ({ draft, updateDraft }: CampaignContentStepProps) => {
  const steps = draft.sequence_steps;

  const setSteps = (sequence_steps: SequenceStepPayload[]) => updateDraft({ sequence_steps });

  const updateStep = (index: number, updates: Partial<SequenceStepPayload>) => {
    const next = steps.map((step, stepIndex) =>
      stepIndex === index ? { ...step, ...updates } : step,
    );
    setSteps(next.map((step, stepIndex) => ({ ...step, step_order: stepIndex + 1 })));
  };

  const addEmail = () =>
    setSteps([
      ...steps,
      {
        step_order: steps.length + 1,
        step_type: "email",
        template_uuid: "",
        subject_override: null,
        body_html_override: null,
        is_enabled: true,
      },
    ]);

  const addDelay = () =>
    setSteps([
      ...steps,
      {
        step_order: steps.length + 1,
        step_type: "delay",
        delay_value: 1,
        delay_unit: "days",
        is_enabled: true,
      },
    ]);

  const removeStep = (index: number) => {
    const next = steps
      .filter((_, stepIndex) => stepIndex !== index)
      .map((step, stepIndex) => ({ ...step, step_order: stepIndex + 1 }));
    setSteps(next);
  };

  const moveStep = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= steps.length) return;
    const next = [...steps];
    [next[index], next[target]] = [next[target], next[index]];
    setSteps(next.map((step, stepIndex) => ({ ...step, step_order: stepIndex + 1 })));
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_330px]">
      <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
              <Mail className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-[#171A22]">Sequence Builder</h2>
              <p className="mt-1 text-sm text-[#756E5C]">
                Add email and delay steps in the exact order recipients should receive them.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={addEmail}
              className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-3.5 py-2.5 text-xs font-semibold text-white"
            >
              <Plus className="h-4 w-4" /> Email
            </button>
            <button
              type="button"
              onClick={addDelay}
              className="inline-flex items-center gap-2 rounded-xl border border-[#D9CFB8] bg-white px-3.5 py-2.5 text-xs font-semibold text-[#615532]"
            >
              <Clock3 className="h-4 w-4" /> Delay
            </button>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          {steps.map((step, index) => (
            <article key={`${step.step_type}-${index}`} className="rounded-2xl border border-[#E5DDCA] bg-[#FFFDF8] p-4 sm:p-5">
              <div className="flex items-center justify-between gap-3 border-b border-[#EEE8DA] pb-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#8F740D] text-xs font-bold text-white">
                    {index + 1}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-[#222731]">
                      {step.step_type === "email" ? "Email Step" : "Delay Step"}
                    </p>
                    <p className="mt-0.5 text-[11px] text-[#817966]">
                      {step.step_type === "email" ? "Send a template" : "Wait before the next email"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button type="button" onClick={() => moveStep(index, -1)} disabled={index === 0} className="rounded-lg p-2 text-[#665F4E] hover:bg-[#F3EDDE] disabled:opacity-30" aria-label="Move step up"><ArrowUp className="h-4 w-4" /></button>
                  <button type="button" onClick={() => moveStep(index, 1)} disabled={index === steps.length - 1} className="rounded-lg p-2 text-[#665F4E] hover:bg-[#F3EDDE] disabled:opacity-30" aria-label="Move step down"><ArrowDown className="h-4 w-4" /></button>
                  <button type="button" onClick={() => removeStep(index)} disabled={steps.length === 1} className="rounded-lg p-2 text-[#B42318] hover:bg-[#FFF1EF] disabled:opacity-30" aria-label="Remove step"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>

              {step.step_type === "email" ? (
                <div className="mt-4 space-y-4">
                  <TemplateSelect
                    label="Template"
                    value={step.template_uuid || ""}
                    onChange={(template_uuid) => updateStep(index, { template_uuid })}
                  />
                  <div className="rounded-xl border border-[#E5DDCA] bg-white p-4">
                    <p className="text-xs font-semibold text-[#403A2E]">Optional step override</p>
                    <p className="mt-1 text-[11px] leading-5 text-[#817966]">
                      Overrides take precedence over the selected template. Without a template, both
                      subject and body are required.
                    </p>
                    <label className="mt-4 block space-y-2">
                      <span className="text-xs font-semibold text-[#403A2E]">Subject override</span>
                      <input
                        value={step.subject_override || ""}
                        onChange={(event) =>
                          updateStep(index, { subject_override: event.target.value || null })
                        }
                        maxLength={255}
                        className={fieldClass}
                      />
                    </label>
                    <div className="mt-4">
                      <span className="mb-2 block text-xs font-semibold text-[#403A2E]">
                        Body override
                      </span>
                      <RichTextEditor
                        value={step.body_html_override || ""}
                        onChange={(body_html_override) =>
                          updateStep(index, { body_html_override: body_html_override || null })
                        }
                      />
                    </div>
                  </div>
                  <label className="flex items-center justify-between rounded-xl border border-[#E5DDCA] bg-white p-3.5">
                    <div>
                      <p className="text-xs font-semibold text-[#302C24]">Enable step</p>
                      <p className="mt-1 text-[11px] text-[#817966]">Disabled steps remain saved but are skipped.</p>
                    </div>
                    <input type="checkbox" checked={step.is_enabled} onChange={(event) => updateStep(index, { is_enabled: event.target.checked })} className="h-5 w-5 accent-[#8F740D]" />
                  </label>
                </div>
              ) : (
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <label className="space-y-2">
                    <span className="text-sm font-semibold text-[#302C24]">Delay *</span>
                    <input type="number" min={1} value={step.delay_value ?? 1} onChange={(event) => updateStep(index, { delay_value: Math.max(1, Number(event.target.value) || 1) })} className={fieldClass} />
                  </label>
                  <label className="space-y-2">
                    <span className="text-sm font-semibold text-[#302C24]">Unit *</span>
                    <AppSelect value={step.delay_unit || "days"} onValueChange={(value) => updateStep(index, { delay_unit: value as DelayUnit })} ariaLabel={`Delay unit for step ${index + 1}`} options={[{ value: "minutes", label: "Minutes" }, { value: "hours", label: "Hours" }, { value: "days", label: "Days" }, { value: "weeks", label: "Weeks" }]} />
                  </label>
                </div>
              )}
            </article>
          ))}
        </div>
      </section>

      <aside className="space-y-5">
        <section className="rounded-2xl border border-[#E8E1D0] bg-[#FFFCF3] p-5">
          <h3 className="font-semibold text-[#171A22]">Sequence Rules</h3>
          <label className="mt-4 flex items-center justify-between rounded-xl border border-[#E5DDCA] bg-white p-3.5">
            <span className="text-sm text-[#4F493C]">Stop on reply</span>
            <input type="checkbox" checked readOnly className="h-5 w-5 accent-[#8F740D]" />
          </label>
          <label className="mt-3 flex items-center justify-between rounded-xl border border-[#E5DDCA] bg-white p-3.5">
            <span className="text-sm text-[#4F493C]">Stop on unsubscribe</span>
            <input type="checkbox" checked readOnly className="h-5 w-5 accent-[#8F740D]" />
          </label>
          <p className="mt-4 text-xs leading-5 text-[#817966]">
            Both stop rules are mandatory in the current campaign backend.
          </p>
        </section>
      </aside>
    </div>
  );
};

const ABTestBuilder = ({ draft, updateDraft }: CampaignContentStepProps) => {
  const variants = draft.ab_variants;
  const updateVariant = (index: number, updates: Partial<ABVariantPayload>) => {
    const next = variants.map((variant, variantIndex) =>
      variantIndex === index ? { ...variant, ...updates } : variant,
    ) as [ABVariantPayload, ABVariantPayload];
    updateDraft({ ab_variants: next });
  };

  const updateAllocation = (value: number) => {
    const allocationA = Math.min(99, Math.max(1, value));
    updateDraft({
      ab_variants: [
        { ...variants[0], allocation_percentage: allocationA },
        { ...variants[1], allocation_percentage: 100 - allocationA },
      ],
    });
  };

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5 sm:p-6">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
            <FlaskConical className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-[#171A22]">A/B Test Content</h2>
            <p className="mt-1 text-sm text-[#756E5C]">
              Configure exactly two variants. Allocation must total 100%.
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-5 xl:grid-cols-2">
          {variants.map((variant, index) => (
            <article key={variant.variant_type} className="rounded-2xl border border-[#E5DDCA] bg-[#FFFDF8] p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#8F740D]">
                    Variant {variant.variant_type.toUpperCase()}
                  </p>
                  <p className="mt-1 text-sm font-semibold text-[#222731]">{variant.name}</p>
                </div>
                <span className="rounded-full bg-[#F8F0D7] px-3 py-1 text-xs font-semibold text-[#735E10]">
                  {variant.allocation_percentage}%
                </span>
              </div>

              <div className="mt-5 space-y-4">
                <label className="block space-y-2">
                  <span className="text-sm font-semibold text-[#302C24]">Variant Name *</span>
                  <input value={variant.name} onChange={(event) => updateVariant(index, { name: event.target.value })} maxLength={50} className={fieldClass} />
                </label>
                <TemplateSelect
                  label="Template"
                  value={variant.template_uuid || ""}
                  onChange={(template_uuid) => updateVariant(index, { template_uuid })}
                />
                <div className="rounded-xl border border-[#E5DDCA] bg-white p-4">
                  <p className="text-xs font-semibold text-[#403A2E]">Optional content override</p>
                  <p className="mt-1 text-[11px] leading-5 text-[#817966]">
                    Overrides take precedence over the selected template. Without a template, both fields are required.
                  </p>
                  <label className="mt-4 block space-y-2">
                    <span className="text-xs font-semibold text-[#403A2E]">Subject override</span>
                    <input value={variant.subject_override || ""} onChange={(event) => updateVariant(index, { subject_override: event.target.value || null })} maxLength={255} className={fieldClass} />
                  </label>
                  <div className="mt-4">
                    <span className="mb-2 block text-xs font-semibold text-[#403A2E]">Body override</span>
                    <RichTextEditor value={variant.body_html_override || ""} onChange={(body_html_override) => updateVariant(index, { body_html_override: body_html_override || null })} />
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-5 rounded-2xl border border-[#E8E1D0] bg-[#FFFCF3] p-5 md:grid-cols-3">
        <label className="space-y-2">
          <span className="text-sm font-semibold text-[#302C24]">Variant A Allocation</span>
          <input type="range" min={1} max={99} value={variants[0].allocation_percentage} onChange={(event) => updateAllocation(Number(event.target.value))} className="w-full accent-[#8F740D]" />
          <p className="text-xs text-[#817966]">A {variants[0].allocation_percentage}% · B {variants[1].allocation_percentage}%</p>
        </label>
        <label className="space-y-2">
          <span className="text-sm font-semibold text-[#302C24]">Test Audience</span>
          <input type="number" min={1} max={100} value={draft.ab_test_percentage} onChange={(event) => updateDraft({ ab_test_percentage: Math.min(100, Math.max(1, Number(event.target.value) || 1)) })} className={fieldClass} />
          <p className="text-xs text-[#817966]">Percentage of campaign recipients included in the test.</p>
        </label>
        <label className="space-y-2">
          <span className="text-sm font-semibold text-[#302C24]">Winner Metric</span>
          <AppSelect value={draft.ab_winner_metric} onValueChange={(value) => updateDraft({ ab_winner_metric: value as CampaignDraft["ab_winner_metric"] })} ariaLabel="Winner metric" options={[{ value: "reply_rate", label: "Reply rate" }, { value: "click_rate", label: "Click rate" }, { value: "open_rate", label: "Open rate" }, { value: "delivery_rate", label: "Delivery rate" }]} />
        </label>
        <label className="flex items-center justify-between rounded-xl border border-[#E5DDCA] bg-white p-4 md:col-span-3">
          <div>
            <p className="text-sm font-semibold text-[#302C24]">Automatically select winner</p>
            <p className="mt-1 text-xs text-[#817966]">Otherwise a winner can be selected manually from campaign details.</p>
          </div>
          <input type="checkbox" checked={draft.ab_auto_select_winner} onChange={(event) => updateDraft({ ab_auto_select_winner: event.target.checked })} className="h-5 w-5 accent-[#8F740D]" />
        </label>
      </section>
    </div>
  );
};

export const CampaignContentStep = (props: CampaignContentStepProps) => {
  if (props.draft.campaign_type === "sequence") return <SequenceBuilder {...props} />;
  if (props.draft.campaign_type === "ab_test") return <ABTestBuilder {...props} />;
  return <StandardContent {...props} />;
};
