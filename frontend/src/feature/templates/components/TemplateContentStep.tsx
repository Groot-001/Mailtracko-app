import { useRef } from "react";
import { Info } from "lucide-react";
import { RichTextEditor, type RichTextEditorHandle } from "./RichTextEditor";
import type { TemplateDraft } from "./TemplateWizard";
import type { TemplateFieldErrors } from "../schema/templateSchema";

interface TemplateContentStepProps {
  draft: TemplateDraft;
  updateDraft: (updates: Partial<TemplateDraft>) => void;
  templateUuid?: string;
  resolveTemplateUuid?: () => Promise<string | null>;
  errors?: TemplateFieldErrors;
}

const mergeVariables = ["{{first_name}}", "{{last_name}}", "{{email}}", "{{company}}", "{{unsubscribe_link}}"];
const fieldClass = (hasError?: boolean) =>
  `h-11 w-full rounded-xl border bg-white px-3.5 text-sm outline-none transition focus:ring-1 ${hasError ? "border-red-400 focus:border-red-500 focus:ring-red-300/30" : "border-[#DED7C7] focus:border-[#A88916] focus:ring-[#E9DFAE]/60"}`;

export const TemplateContentStep = ({
  draft,
  updateDraft,
  templateUuid,
  resolveTemplateUuid,
  errors = {},
}: TemplateContentStepProps) => {
  const editorRef = useRef<RichTextEditorHandle>(null);

  return (
    <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1fr)_280px]">
      <div className="min-w-0 space-y-5">
        <div className="grid min-w-0 gap-4 md:grid-cols-2">
          <label className="min-w-0 space-y-2">
            <span className="text-sm font-semibold text-[#302C24]">Template Name *</span>
            <input
              value={draft.name}
              onChange={(event) => updateDraft({ name: event.target.value })}
              maxLength={50}
              aria-invalid={Boolean(errors.name)}
              placeholder="Welcome Email – New Subscribers"
              className={fieldClass(Boolean(errors.name))}
            />
            {errors.name ? <p role="alert" className="text-xs font-medium text-red-600">{errors.name}</p> : null}
          </label>
          <label className="min-w-0 space-y-2">
            <span className="text-sm font-semibold text-[#302C24]">Subject Line *</span>
            <input
              value={draft.subject}
              onChange={(event) => updateDraft({ subject: event.target.value })}
              maxLength={255}
              aria-invalid={Boolean(errors.subject)}
              placeholder="Welcome to {{company}}, {{first_name}}!"
              className={fieldClass(Boolean(errors.subject))}
            />
            {errors.subject ? <p role="alert" className="text-xs font-medium text-red-600">{errors.subject}</p> : null}
          </label>
        </div>
        <label className="block min-w-0 space-y-2">
          <span className="text-sm font-semibold text-[#302C24]">Preview Text</span>
          <input
            value={draft.preheader}
            onChange={(event) => updateDraft({ preheader: event.target.value })}
            maxLength={255}
            aria-invalid={Boolean(errors.preheader)}
            placeholder="Here’s what you can expect and how to get started."
            className={fieldClass(Boolean(errors.preheader))}
          />
          <div className="flex justify-between gap-3 text-xs text-[#8B8371]">
            <span>{errors.preheader ? <span role="alert" className="font-medium text-red-600">{errors.preheader}</span> : "Optional"}</span>
            <span>{draft.preheader.length}/255</span>
          </div>
        </label>
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <span className="text-sm font-semibold text-[#302C24]">Email Body *</span>
            <span className="text-xs text-[#8B8371]">HTML is generated from the editor automatically.</span>
          </div>
          <RichTextEditor
            ref={editorRef}
            templateUuid={templateUuid}
            resolveTemplateUuid={resolveTemplateUuid}
            value={draft.body_html}
            error={errors.body_html}
            onChange={(body_html) => updateDraft({ body_html })}
          />
        </div>
      </div>

      <aside className="min-w-0 self-start rounded-2xl border border-[#E5DDCA] bg-[#FFFCF3] p-5">
        <div className="flex items-center gap-2 text-sm font-semibold text-[#3F371C]">
          <Info className="h-4 w-4 text-[#8F740D]" /> Merge Variables
        </div>
        <p className="mt-2 text-xs leading-5 text-[#766D54]">
          Place the cursor in the email body, then choose a variable. It will be inserted exactly at that cursor position.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {mergeVariables.map((variable) => (
            <button
              type="button"
              key={variable}
              onClick={() => editorRef.current?.insertMergeVariable(variable)}
              className="max-w-full break-all rounded-lg border border-[#DCCF9A] bg-white px-2.5 py-1.5 text-xs font-medium text-[#705A0A] hover:bg-[#F8F0D7]"
            >
              {variable}
            </button>
          ))}
        </div>
        <div className="mt-5 rounded-xl border border-[#EADCB2] bg-white p-3 text-xs leading-5 text-[#6D654F]">
          Always include <strong>{"{{unsubscribe_link}}"}</strong> in outreach templates before publishing.
        </div>
      </aside>
    </div>
  );
};
