import { useEffect, useState } from "react";
import { CalendarClock, Clock3, Send } from "lucide-react";
import { AppSelect } from "../../../shared/components/AppSelect";
import type { CampaignDraft } from "./CampaignWizard";

interface CampaignScheduleStepProps {
  draft: CampaignDraft;
  updateDraft: (updates: Partial<CampaignDraft>) => void;
}

const timezoneOptions = [
  "UTC",
  "Asia/Kathmandu",
  "Asia/Kolkata",
  "Europe/London",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
];

export const CampaignScheduleStep = ({ draft, updateDraft }: CampaignScheduleStepProps) => {
  const [batchSizeInput, setBatchSizeInput] = useState(String(draft.batch_size));

  useEffect(() => {
    setBatchSizeInput(String(draft.batch_size));
  }, [draft.batch_size]);

  const commitBatchSize = () => {
    const parsed = Number(batchSizeInput);
    const normalized = Number.isInteger(parsed) && parsed >= 1 && parsed <= 500
      ? parsed
      : Math.min(500, Math.max(1, Number.isFinite(parsed) ? Math.round(parsed) : 25));
    setBatchSizeInput(String(normalized));
    if (normalized !== draft.batch_size) updateDraft({ batch_size: normalized });
  };

  return (
  <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
    <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5 sm:p-6">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
          <CalendarClock className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-[#171A22]">Schedule Campaign</h2>
          <p className="mt-1 text-sm text-[#756E5C]">
            Launch immediately after review or choose one future date and time.
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <button
          type="button"
          onClick={() => updateDraft({ delivery_mode: "immediate" })}
          className={`rounded-2xl border p-5 text-left transition ${
            draft.delivery_mode === "immediate"
              ? "border-[#B99A22] bg-[#FFFCF3] ring-2 ring-[#EDE2B5]"
              : "border-[#E5DDCA] hover:border-[#CDBF8E]"
          }`}
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
            <Send className="h-5 w-5" />
          </div>
          <p className="mt-4 text-sm font-semibold text-[#222731]">Send Now</p>
          <p className="mt-1 text-xs leading-5 text-[#77705E]">
            Launch after the backend review confirms the campaign is ready.
          </p>
        </button>

        <button
          type="button"
          onClick={() => updateDraft({ delivery_mode: "scheduled" })}
          className={`rounded-2xl border p-5 text-left transition ${
            draft.delivery_mode === "scheduled"
              ? "border-[#B99A22] bg-[#FFFCF3] ring-2 ring-[#EDE2B5]"
              : "border-[#E5DDCA] hover:border-[#CDBF8E]"
          }`}
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
            <Clock3 className="h-5 w-5" />
          </div>
          <p className="mt-4 text-sm font-semibold text-[#222731]">Schedule for Later</p>
          <p className="mt-1 text-xs leading-5 text-[#77705E]">
            Select a one-time future date and timezone.
          </p>
        </button>
      </div>

      {draft.delivery_mode === "scheduled" && (
        <div className="mt-6 grid gap-5 rounded-2xl border border-[#E5DDCA] bg-[#FFFDF8] p-5 md:grid-cols-2">
          <label className="space-y-2">
            <span className="text-sm font-semibold text-[#302C24]">Date & Time *</span>
            <input
              type="datetime-local"
              value={draft.scheduled_at_local}
              onChange={(event) => updateDraft({ scheduled_at_local: event.target.value })}
              className="h-11 w-full rounded-xl border border-[#DED7C7] bg-white px-3 text-sm outline-none focus:border-[#A88916] focus:ring-2 focus:ring-[#E9DFAE]"
            />
          </label>
          <label className="space-y-2">
            <span className="text-sm font-semibold text-[#302C24]">Timezone *</span>
            <AppSelect value={draft.timezone} onValueChange={(value) => updateDraft({ timezone: value })} ariaLabel="Campaign timezone" searchable options={timezoneOptions.map((timezone) => ({ value: timezone, label: timezone }))} />
          </label>
        </div>
      )}

      <div className="mt-6 grid gap-5 md:grid-cols-2">
        <label className="space-y-2">
          <span className="text-sm font-semibold text-[#302C24]">Daily Sending Limit</span>
          <input
            type="number"
            min={1}
            value={draft.daily_limit ?? ""}
            onChange={(event) =>
              updateDraft({ daily_limit: event.target.value ? Math.max(1, Number(event.target.value)) : null })
            }
            placeholder="Use account limit"
            className="h-11 w-full rounded-xl border border-[#DED7C7] px-3.5 text-sm outline-none focus:border-[#A88916] focus:ring-2 focus:ring-[#E9DFAE]"
          />
          <p className="text-xs text-[#817966]">Leave empty to use the campaign backend default.</p>
        </label>
        <label className="space-y-2">
          <span className="text-sm font-semibold text-[#302C24]">Batch Size</span>
          <input
            type="number"
            min={1}
            max={500}
            value={batchSizeInput}
            onChange={(event) => {
              const value = event.target.value;
              if (value === "" || /^\d{1,3}$/.test(value)) setBatchSizeInput(value);
            }}
            onBlur={commitBatchSize}
            className="h-11 w-full rounded-xl border border-[#DED7C7] px-3.5 text-sm outline-none focus:border-[#A88916] focus:ring-2 focus:ring-[#E9DFAE]"
          />
          <p className="text-xs text-[#817966]">Enter a whole number from 1 to 500. You can clear the field while editing.</p>
        </label>
      </div>
    </section>

    <aside className="rounded-2xl border border-[#E8E1D0] bg-[#FFFCF3] p-5">
      <h3 className="font-semibold text-[#171A22]">Schedule Summary</h3>
      <dl className="mt-5 space-y-4 text-sm">
        <div>
          <dt className="text-xs text-[#817966]">Delivery</dt>
          <dd className="mt-1 font-semibold text-[#292D36]">
            {draft.delivery_mode === "immediate" ? "Send immediately" : "One-time schedule"}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-[#817966]">Timezone</dt>
          <dd className="mt-1 font-semibold text-[#292D36]">{draft.timezone}</dd>
        </div>
        <div>
          <dt className="text-xs text-[#817966]">Daily limit</dt>
          <dd className="mt-1 font-semibold text-[#292D36]">
            {draft.daily_limit?.toLocaleString() || "Account/default limit"}
          </dd>
        </div>
      </dl>
      <p className="mt-5 rounded-xl border border-[#EADCB2] bg-white p-3 text-xs leading-5 text-[#6D654F]">
        Advanced sending windows, business-day rules, and recurring schedules are intentionally excluded from this scope.
      </p>
    </aside>
  </div>
  );
};
