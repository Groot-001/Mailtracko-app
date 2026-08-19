import { CheckCircle2, ListFilter, Users } from "lucide-react";
import { useContactListCount, useContactLists } from "../../../shared/api/useWorkspaceData";
import { InlineNotice } from "../../../shared/components/InlineNotice";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import type { CampaignDraft } from "./CampaignWizard";

interface CampaignAudienceStepProps {
  draft: CampaignDraft;
  updateDraft: (updates: Partial<CampaignDraft>) => void;
}

export const CampaignAudienceStep = ({ draft, updateDraft }: CampaignAudienceStepProps) => {
  const listsQuery = useContactLists();
  const countQuery = useContactListCount(draft.contact_list_uuid || undefined);
  const selectedList = listsQuery.data?.items.find(
    (list) => list.uuid === draft.contact_list_uuid,
  );

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5 sm:p-6">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-[#171A22]">Choose Audience</h2>
            <p className="mt-1 text-sm text-[#756E5C]">
              Choose one organization collection for this campaign.
            </p>
          </div>
        </div>

        {listsQuery.isError ? (
          <div className="mt-6">
            <InlineNotice tone="error">
              {getApiErrorMessage(listsQuery.error, "Collections could not be loaded.")}
            </InlineNotice>
          </div>
        ) : listsQuery.isLoading ? (
          <div className="mt-6 space-y-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-20 animate-pulse rounded-xl bg-[#F3F0E8]" />
            ))}
          </div>
        ) : listsQuery.data?.items.length ? (
          <div className="mt-6 grid gap-3 md:grid-cols-2">
            {listsQuery.data.items.map((list) => {
              const selected = list.uuid === draft.contact_list_uuid;
              return (
                <button
                  key={list.uuid}
                  type="button"
                  onClick={() => updateDraft({ contact_list_uuid: list.uuid })}
                  className={`rounded-xl border p-4 text-left transition ${
                    selected
                      ? "border-[#B99A22] bg-[#FFFCF3] ring-2 ring-[#EDE2B5]"
                      : "border-[#E5DDCA] bg-white hover:border-[#CDBF8E] hover:bg-[#FFFDF8]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
                      <ListFilter className="h-5 w-5" />
                    </div>
                    {selected && <CheckCircle2 className="h-5 w-5 text-[#8F740D]" />}
                  </div>
                  <p className="mt-4 text-sm font-semibold text-[#222731]">{list.name}</p>
                  <p className="mt-1 line-clamp-2 min-h-10 text-xs leading-5 text-[#77705E]">
                    {list.description || "Organization collection"}
                  </p>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="mt-6 rounded-xl border border-dashed border-[#D9CFB8] bg-[#FCFAF4] px-5 py-10 text-center">
            <Users className="mx-auto h-7 w-7 text-[#8F740D]" />
            <p className="mt-3 text-sm font-semibold text-[#292D36]">No collections available</p>
            <p className="mt-1 text-xs text-[#817966]">
              Create or import a collection before launching a campaign.
            </p>
          </div>
        )}
      </section>

      <aside className="space-y-5">
        <section className="rounded-2xl border border-[#E8E1D0] bg-[#FFFCF3] p-5">
          <h3 className="font-semibold text-[#171A22]">Audience Summary</h3>
          <div className="mt-5 rounded-xl border border-[#E5DDCA] bg-white p-4">
            <p className="text-xs text-[#817966]">Selected collection</p>
            <p className="mt-1 text-sm font-semibold text-[#292D36]">
              {selectedList?.name || "No collection selected"}
            </p>
          </div>
          <div className="mt-3 rounded-xl border border-[#E5DDCA] bg-white p-4">
            <p className="text-xs text-[#817966]">Contacts</p>
            <p className="mt-1 text-2xl font-bold text-[#171A22]">
              {countQuery.isLoading ? "…" : (countQuery.data ?? 0).toLocaleString()}
            </p>
            <p className="mt-1 text-xs text-[#817966]">Current collection total</p>
          </div>
        </section>

        <InlineNotice>
          Email verification is optional for campaign contacts. Unverified contacts can be sent in bulk;
          MailTracko excludes malformed, unsubscribed, suppressed, archived, hard-bounced, confirmed-invalid,
          and duplicate recipients during campaign review.
        </InlineNotice>
      </aside>
    </div>
  );
};
