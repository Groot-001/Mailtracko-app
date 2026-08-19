import { useEffect, useMemo, useState } from "react";
import { Check, FilePlus2, Search, Sparkles } from "lucide-react";
import { AppSelect } from "../../../shared/components/AppSelect";
import { InlineNotice } from "../../../shared/components/InlineNotice";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import {
  useCopySystemTemplate,
  useSystemTemplates,
  useSystemTemplateCategories,
} from "../hooks/useTemplates";
import type { EmailTemplate } from "../types/template.types";

interface TemplateGalleryStepProps {
  onBlank: () => void;
  onCopied: (template: EmailTemplate) => void;
}

export const TemplateGalleryStep = ({ onBlank, onCopied }: TemplateGalleryStepProps) => {
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [selectedUuid, setSelectedUuid] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const categoriesQuery = useSystemTemplateCategories();
  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(searchInput.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [searchInput]);
  const params = useMemo(
    () => ({ search, category_id: categoryId, limit: 18, offset: 0 }),
    [categoryId, search],
  );
  const galleryQuery = useSystemTemplates(params);
  const copyMutation = useCopySystemTemplate();

  const useSelected = async () => {
    if (!selectedUuid) return;
    setError(null);
    try {
      const template = (await copyMutation.mutateAsync(selectedUuid)) as EmailTemplate;
      onCopied(template);
    } catch (copyError) {
      setError(getApiErrorMessage(copyError, "The selected template could not be copied."));
    }
  };

  return (
    <div>
      <div className="flex flex-col gap-3 md:flex-row md:items-center">
        <label className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#938A74]" />
          <input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search the template gallery..."
            className="h-11 w-full rounded-xl border border-[#DED7C7] bg-white pl-10 pr-3 text-sm outline-none focus:border-[#A88916] focus:ring-1 focus:ring-[#E9DFAE]/60"
          />
        </label>
        <AppSelect className="min-w-52" value={categoryId?.toString() ?? ""} onValueChange={(value) => setCategoryId(value ? Number(value) : undefined)} ariaLabel="Filter templates by category" searchable options={[{ value: "", label: "All Categories" }, ...(categoriesQuery.data?.map((category) => ({ value: category.id.toString(), label: category.name })) ?? [])]} />
      </div>

      {error && (
        <div className="mt-4">
          <InlineNotice tone="error">{error}</InlineNotice>
        </div>
      )}

      <button
        type="button"
        onClick={onBlank}
        className="mt-5 flex w-full items-center gap-4 rounded-2xl border border-dashed border-[#CDBB76] bg-[#FFFCF2] p-5 text-left transition hover:border-[#9A7E16] hover:bg-[#FFF8DD]"
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F4EACB] text-[#8F740D]">
          <FilePlus2 className="h-6 w-6" />
        </div>
        <div>
          <p className="font-semibold text-[#171A22]">Start with a blank template</p>
          <p className="mt-1 text-sm text-[#756E5C]">Create a reusable email using the Phase 1 rich-text editor.</p>
        </div>
      </button>

      {galleryQuery.isError ? (
        <div className="mt-5">
          <InlineNotice tone="error">
            {getApiErrorMessage(galleryQuery.error, "The template gallery could not be loaded.")}
          </InlineNotice>
        </div>
      ) : galleryQuery.isLoading && !galleryQuery.data ? (
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="h-56 animate-pulse rounded-2xl bg-[#F4F0E6]" />
          ))}
        </div>
      ) : (
        <div className={`mt-5 grid gap-4 transition-opacity md:grid-cols-2 xl:grid-cols-3 ${galleryQuery.isFetching ? "opacity-75" : "opacity-100"}`}>
          {galleryQuery.data?.items.map((template, index) => {
            const selected = selectedUuid === template.uuid;
            return (
              <button
                type="button"
                key={template.uuid}
                onClick={() => setSelectedUuid(template.uuid)}
                className={`group overflow-hidden rounded-2xl border bg-white text-left transition ${
                  selected
                    ? "border-[#9A7E16] ring-1 ring-[#9A7E16]/60"
                    : "border-[#E8E1D0] hover:border-[#CCBC7D] hover:shadow-lg"
                }`}
              >
                <div className="relative flex h-36 items-center justify-center bg-gradient-to-br from-[#FFFDF5] to-[#F2E8C8] p-5">
                  <div className="w-full rounded-xl border border-white/80 bg-white/90 p-4 shadow-sm">
                    <div className="flex items-center gap-2 text-[10px] font-semibold text-[#8F740D]">
                      <Sparkles className="h-3.5 w-3.5" /> MailTracko
                    </div>
                    <p className="mt-3 line-clamp-1 text-sm font-bold text-[#19202D]">{template.subject}</p>
                    <div className="mt-3 h-2 w-3/4 rounded bg-[#ECE5D5]" />
                    <div className="mt-1.5 h-2 w-1/2 rounded bg-[#F1ECDF]" />
                  </div>
                  {selected && (
                    <span className="absolute right-3 top-3 flex h-7 w-7 items-center justify-center rounded-full bg-[#8F740D] text-white">
                      <Check className="h-4 w-4" />
                    </span>
                  )}
                </div>
                <div className="p-4">
                  <p className="font-semibold text-[#171A22]">{template.name}</p>
                  <p className="mt-1 line-clamp-2 min-h-10 text-sm leading-5 text-[#756E5C]">
                    {template.description || "Pre-built email template ready to customize."}
                  </p>
                  <span className="mt-3 inline-flex rounded-lg bg-[#F7F0DA] px-2.5 py-1 text-xs text-[#735E10]">
                    Template {index + 1}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}

      <div className="mt-6 flex justify-end">
        <button
          type="button"
          disabled={!selectedUuid || copyMutation.isPending}
          onClick={useSelected}
          className="rounded-xl bg-[#8F740D] px-5 py-3 text-sm font-semibold text-white shadow-button disabled:cursor-not-allowed disabled:opacity-45"
        >
          {copyMutation.isPending ? "Preparing Template..." : "Use Selected Template"}
        </button>
      </div>
    </div>
  );
};
