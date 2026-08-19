import { Plus, Tag, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useCreateTemplateCategory, useTemplateCategories } from "../hooks/useTemplates";
import { AppSelect } from "../../../shared/components/AppSelect";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import type { TemplateDraft } from "./TemplateWizard";
import type { TemplateFieldErrors } from "../schema/templateSchema";

const SHORT_FIELD_LIMIT = 50;
const fieldClass = (hasError?: boolean) =>
  `h-11 w-full min-w-0 rounded-xl border bg-white px-3.5 text-sm outline-none transition focus:ring-1 ${hasError ? "border-red-400 focus:border-red-500 focus:ring-red-300/30" : "border-[#DED7C7] focus:border-[#A88916] focus:ring-[#E9DFAE]/60"}`;

interface TemplateSettingsStepProps {
  draft: TemplateDraft;
  updateDraft: (updates: Partial<TemplateDraft>) => void;
  errors?: TemplateFieldErrors;
}

export const TemplateSettingsStep = ({ draft, updateDraft, errors = {} }: TemplateSettingsStepProps) => {
  const categoriesQuery = useTemplateCategories();
  const createCategory = useCreateTemplateCategory();
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [categoryName, setCategoryName] = useState("");
  const [categoryError, setCategoryError] = useState<string | null>(null);
  const categoryInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!showCategoryForm) return;
    const timer = window.setTimeout(() => categoryInputRef.current?.focus({ preventScroll: true }), 0);
    return () => window.clearTimeout(timer);
  }, [showCategoryForm]);

  const handleCreateCategory = async () => {
    const name = categoryName.trim();
    if (!name) {
      setCategoryError("Enter a category name.");
      return;
    }
    if (name.length > SHORT_FIELD_LIMIT) {
      setCategoryError(`Maximum ${SHORT_FIELD_LIMIT} characters allowed.`);
      return;
    }
    setCategoryError(null);
    try {
      const category = await createCategory.mutateAsync({ name });
      updateDraft({ category_id: category.id });
      setCategoryName("");
      setShowCategoryForm(false);
    } catch (error) {
      setCategoryError(getApiErrorMessage(error, "Failed to create category."));
    }
  };

  return (
    <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(280px,360px)]">
      <div className="min-w-0 overflow-hidden rounded-2xl border border-[#E8E1D0] bg-white p-5 sm:p-6">
        <h2 className="text-lg font-semibold text-[#171A22]">Template Settings</h2>
        <p className="mt-1 text-sm text-[#756E5C]">Configure optional sender metadata, categories, and organization defaults.</p>

        <div className="mt-6 grid min-w-0 gap-5 md:grid-cols-2">
          <div className="min-w-0 space-y-2">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-semibold text-[#302C24]">Category</span>
              <button
                type="button"
                onClick={() => {
                  setShowCategoryForm((current) => !current);
                  setCategoryError(null);
                }}
                className="inline-flex items-center gap-1 text-xs font-semibold text-[#80680C] hover:text-[#5E4C08]"
              >
                {showCategoryForm ? <X className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
                {showCategoryForm ? "Cancel" : "New category"}
              </button>
            </div>
            <AppSelect value={draft.category_id?.toString() ?? ""} onValueChange={(value) => updateDraft({ category_id: value ? Number(value) : null })} ariaLabel="Template category" searchable options={[{ value: "", label: "Uncategorized" }, ...(categoriesQuery.data?.map((category) => ({ value: category.id.toString(), label: category.name })) ?? [])]} />
            {showCategoryForm && (
              <div className="min-w-0 rounded-xl border border-[#E6DFCF] bg-[#FCFBF7] p-3">
                <div className="flex min-w-0 flex-col gap-2 sm:flex-row">
                  <input
                    ref={categoryInputRef}
                    value={categoryName}
                    maxLength={SHORT_FIELD_LIMIT}
                    onChange={(event) => {
                      setCategoryName(event.target.value);
                      setCategoryError(null);
                    }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        event.preventDefault();
                        void handleCreateCategory();
                      }
                    }}
                    placeholder="e.g. Product updates"
                    className="h-10 min-w-0 flex-1 rounded-lg border border-[#DED7C7] bg-white px-3 text-sm outline-none focus:border-[#A88916] focus:ring-1 focus:ring-[#E9DFAE]/60"
                  />
                  <button
                    type="button"
                    disabled={createCategory.isPending}
                    onClick={() => void handleCreateCategory()}
                    className="h-10 shrink-0 rounded-lg bg-[#8F740D] px-3 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {createCategory.isPending ? "Adding..." : "Add"}
                  </button>
                </div>
                {categoryError && <p role="alert" className="mt-2 text-xs font-medium text-red-600">{categoryError}</p>}
                <p className="mt-2 text-[11px] leading-4 text-[#817966]">Custom categories are private to this organization.</p>
              </div>
            )}
          </div>

          <label className="min-w-0 space-y-2">
            <span className="text-sm font-semibold text-[#302C24]">Tags</span>
            <input
              value={draft.tags.join(", ")}
              onChange={(event) => updateDraft({ tags: event.target.value.split(",").map((tag) => tag.trim()).filter(Boolean) })}
              placeholder="welcome, onboarding"
              aria-invalid={Boolean(errors.tags)}
              className={fieldClass(Boolean(errors.tags))}
            />
            {errors.tags ? <span role="alert" className="block text-xs font-medium text-red-600">{errors.tags}</span> : <span className="block text-xs text-[#817966]">Up to 20 tags, 50 characters each.</span>}
          </label>

          <label className="min-w-0 space-y-2">
            <span className="text-sm font-semibold text-[#302C24]">From Name</span>
            <input
              value={draft.from_name}
              maxLength={SHORT_FIELD_LIMIT}
              onChange={(event) => updateDraft({ from_name: event.target.value })}
              placeholder="The {{company}} Team"
              aria-invalid={Boolean(errors.from_name)}
              className={fieldClass(Boolean(errors.from_name))}
            />
            {errors.from_name ? <span role="alert" className="block text-xs font-medium text-red-600">{errors.from_name}</span> : null}
          </label>

          <label className="min-w-0 space-y-2">
            <span className="text-sm font-semibold text-[#302C24]">From Email</span>
            <input
              type="email"
              value={draft.from_email}
              maxLength={SHORT_FIELD_LIMIT}
              onChange={(event) => updateDraft({ from_email: event.target.value })}
              placeholder="hello@yourcompany.com"
              aria-invalid={Boolean(errors.from_email)}
              className={fieldClass(Boolean(errors.from_email))}
            />
            {errors.from_email ? <span role="alert" className="block text-xs font-medium text-red-600">{errors.from_email}</span> : null}
          </label>
        </div>

        <label className="mt-5 block min-w-0 space-y-2">
          <span className="text-sm font-semibold text-[#302C24]">Description</span>
          <textarea
            value={draft.description}
            maxLength={500}
            onChange={(event) => updateDraft({ description: event.target.value })}
            rows={4}
            aria-invalid={Boolean(errors.description)}
            placeholder="Explain when your team should use this template."
            className={`w-full min-w-0 resize-y rounded-xl border bg-white px-3.5 py-3 text-sm outline-none transition focus:ring-1 ${errors.description ? "border-red-400 focus:border-red-500 focus:ring-red-300/30" : "border-[#DED7C7] focus:border-[#A88916] focus:ring-[#E9DFAE]/60"}`}
          />
          <div className="flex justify-between gap-3 text-xs text-[#817966]">
            <span>{errors.description ? <span role="alert" className="font-medium text-red-600">{errors.description}</span> : "Optional"}</span>
            <span>{draft.description.length}/500</span>
          </div>
        </label>

        <label className="mt-5 flex min-w-0 cursor-pointer items-center justify-between gap-4 rounded-xl border border-[#E6DFCF] bg-[#FCFBF7] p-4">
          <div className="min-w-0">
            <p className="text-sm font-semibold text-[#292D36]">Make this the default template</p>
            <p className="mt-1 break-words text-xs text-[#797260]">The backend will mark this template as the organization default.</p>
          </div>
          <input type="checkbox" checked={draft.is_default} onChange={(event) => updateDraft({ is_default: event.target.checked })} className="h-5 w-5 shrink-0 accent-[#8F740D]" />
        </label>
      </div>

      <aside className="min-w-0 self-start overflow-hidden rounded-2xl border border-[#E8E1D0] bg-white p-5">
        <h3 className="font-semibold text-[#171A22]">Live Inbox Preview</h3>
        <p className="mt-1 text-xs text-[#817966]">A simple preview of the sender, subject, and preheader.</p>
        <div className="mt-5 min-w-0 overflow-hidden rounded-2xl border border-[#E6DFCF] bg-[#FFFEFB] p-4 shadow-sm">
          <div className="flex min-w-0 gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#F4EACB] text-xs font-bold text-[#79610A]">MT</div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-[#171A22]">{draft.from_name || "MailTracko Team"}</p>
              <p className="mt-0.5 truncate text-sm font-medium text-[#343945]">{draft.subject || "Your subject line"}</p>
              <p className="mt-1 line-clamp-2 break-words text-xs leading-5 text-[#77705E]">{draft.preheader || "Preview text will appear here when provided."}</p>
            </div>
          </div>
        </div>
        <div className="mt-5 flex min-w-0 items-center gap-2 rounded-xl bg-[#FFF8E3] p-3 text-xs text-[#6F5C17]">
          <Tag className="h-4 w-4 shrink-0" /> <span className="min-w-0 break-words">{draft.tags.length ? `${draft.tags.length} tag(s) applied` : "No tags applied"}</span>
        </div>
      </aside>
    </div>
  );
};
