import { FlaskConical, Layers3, Mail, Sparkles } from "lucide-react";
import { AppSelect } from "../../../shared/components/AppSelect";
import type { CampaignDraft } from "./CampaignWizard";
import type { CampaignGoal, CampaignType } from "../types/campaign.types";

interface CampaignSetupStepProps {
  draft: CampaignDraft;
  updateDraft: (updates: Partial<CampaignDraft>) => void;
  campaignTypeLocked?: boolean;
}

const campaignTypes: Array<{
  value: CampaignType;
  title: string;
  description: string;
  icon: typeof Mail;
}> = [
  {
    value: "regular",
    title: "Standard Campaign",
    description: "Send one reusable template to a selected collection.",
    icon: Mail,
  },
  {
    value: "sequence",
    title: "Email Sequence",
    description: "Build a campaign with email and delay steps.",
    icon: Layers3,
  },
  {
    value: "ab_test",
    title: "A/B Test",
    description: "Compare two campaign content variants and select a winner.",
    icon: FlaskConical,
  },
];

const goals: Array<{ value: CampaignGoal; label: string }> = [
  { value: "outreach", label: "Outreach" },
  { value: "sales", label: "Sales" },
  { value: "lead_generation", label: "Lead Generation" },
  { value: "follow_up", label: "Follow Up" },
  { value: "newsletter", label: "Newsletter" },
  { value: "custom", label: "Custom" },
];

export const CampaignSetupStep = ({
  draft,
  updateDraft,
  campaignTypeLocked = false,
}: CampaignSetupStepProps) => (
  <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_330px]">
    <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5 sm:p-6">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-[#171A22]">Campaign Setup</h2>
          <p className="mt-1 text-sm text-[#756E5C]">
            Add the basic information that identifies this campaign.
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <label className="space-y-2 md:col-span-2">
          <span className="text-sm font-semibold text-[#302C24]">Campaign Name *</span>
          <input
            value={draft.name}
            onChange={(event) => updateDraft({ name: event.target.value })}
            maxLength={50}
            placeholder="Q3 Product Outreach"
            className="h-11 w-full rounded-xl border border-[#DED7C7] px-3.5 text-sm outline-none focus:border-[#A88916] focus:ring-2 focus:ring-[#E9DFAE]"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-semibold text-[#302C24]">Campaign Goal</span>
          <AppSelect value={draft.goal} onValueChange={(value) => updateDraft({ goal: value as CampaignGoal })} ariaLabel="Campaign goal" options={goals.map((goal) => ({ value: goal.value, label: goal.label }))} />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-semibold text-[#302C24]">Priority</span>
          <AppSelect value={draft.priority} onValueChange={(value) => updateDraft({ priority: value as CampaignDraft["priority"] })} ariaLabel="Campaign priority" options={[{ value: "low", label: "Low" }, { value: "normal", label: "Normal" }, { value: "high", label: "High" }, { value: "critical", label: "Critical" }]} />
        </label>
      </div>

      <label className="mt-5 block space-y-2">
        <span className="text-sm font-semibold text-[#302C24]">Description</span>
        <textarea
          value={draft.description}
          onChange={(event) => updateDraft({ description: event.target.value })}
          maxLength={1000}
          rows={4}
          placeholder="Describe the audience and purpose of this campaign."
          className="w-full rounded-xl border border-[#DED7C7] px-3.5 py-3 text-sm outline-none focus:border-[#A88916] focus:ring-2 focus:ring-[#E9DFAE]"
        />
        <span className="block text-right text-[11px] text-[#918A78]">
          {draft.description.length}/1000
        </span>
      </label>
    </section>

    <aside className="rounded-2xl border border-[#E8E1D0] bg-[#FFFCF3] p-5">
      <h3 className="font-semibold text-[#171A22]">Campaign Type</h3>
      <p className="mt-1 text-xs leading-5 text-[#817966]">
        Sequence and A/B testing are campaign-level options. The backend locks the type after
        campaign creation.
      </p>
      <div className="mt-4 space-y-3">
        {campaignTypes.map(({ value, title, description, icon: Icon }) => {
          const selected = draft.campaign_type === value;
          return (
            <button
              key={value}
              type="button"
              disabled={campaignTypeLocked}
              onClick={() => updateDraft({ campaign_type: value })}
              className={`w-full rounded-xl border p-3.5 text-left transition ${
                selected
                  ? "border-[#B99A22] bg-white shadow-sm ring-2 ring-[#EDE2B5]"
                  : "border-[#E5DDCA] bg-white/70 hover:border-[#CDBF8E]"
              } disabled:cursor-not-allowed disabled:opacity-70`}
            >
              <div className="flex gap-3">
                <div
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                    selected ? "bg-[#8F740D] text-white" : "bg-[#F5F0E1] text-[#776C4B]"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-[#292D36]">{title}</p>
                  <p className="mt-1 text-xs leading-5 text-[#77705E]">{description}</p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  </div>
);
