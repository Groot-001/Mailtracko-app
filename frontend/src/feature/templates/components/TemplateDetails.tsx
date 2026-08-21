import { Link, useNavigate } from "@tanstack/react-router";
import { Archive, ArrowLeft, Copy, Edit3, FileText, Send, Trash2 } from "lucide-react";
import { useState } from "react";
import { useToast } from "../../../shared/hooks/useToast";
import { EmailPreviewFrame } from "../../../shared/components/EmailPreviewFrame";
import { InlineNotice } from "../../../shared/components/InlineNotice";
import { Modal } from "../../../shared/components/Modal";
import { PageContainer, PageHeader, PageSection } from "../../../shared/components/layout";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import {
  useArchiveTemplate,
  useDeleteTemplate,
  useDuplicateTemplate,
  usePublishTemplate,
  useRestoreTemplate,
  useTemplate,
  useTemplateCategories,
} from "../hooks/useTemplates";
import { formatTemplateDate, statusLabel } from "../utils/templateFormatters";
import { getTemplateCampaignUsage } from "../api/templateApi";

interface TemplateDetailsProps {
  templateUuid: string;
}

export const TemplateDetails = ({ templateUuid }: TemplateDetailsProps) => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const templateQuery = useTemplate(templateUuid);
  const categoriesQuery = useTemplateCategories();
  const publishMutation = usePublishTemplate();
  const archiveMutation = useArchiveTemplate();
  const restoreMutation = useRestoreTemplate();
  const duplicateMutation = useDuplicateTemplate();
  const deleteMutation = useDeleteTemplate();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmArchive, setConfirmArchive] = useState(false);
  const [confirmRestore, setConfirmRestore] = useState(false);
  const [blockedLifecycle, setBlockedLifecycle] = useState<"archive" | "delete" | null>(null);
  const [checkingLifecycle, setCheckingLifecycle] = useState(false);
  const [feedback, setFeedback] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  if (templateQuery.isLoading) {
    return (
      <PageContainer>
        <div className="h-[680px] animate-pulse rounded-2xl bg-[#F0ECE2]" />
      </PageContainer>
    );
  }

  if (templateQuery.isError || !templateQuery.data) {
    return (
      <PageContainer>
        <InlineNotice tone="error">
          {getApiErrorMessage(templateQuery.error, "Template could not be loaded.")}
        </InlineNotice>
      </PageContainer>
    );
  }

  const template = templateQuery.data;
  const category = categoriesQuery.data?.find((item) => item.id === template.category_id);
  const canEdit = template.status === "draft";

  const prepareLifecycleAction = async (operation: "archive" | "delete") => {
    setFeedback(null);
    setCheckingLifecycle(true);
    try {
      const usage = await getTemplateCampaignUsage(templateUuid);
      if (usage.in_use) {
        setBlockedLifecycle(operation);
        return;
      }
      if (operation === "archive") setConfirmArchive(true);
      else setConfirmDelete(true);
    } catch (error) {
      setFeedback({ tone: "error", text: getApiErrorMessage(error, "Unable to check whether this template is used by a campaign.") });
    } finally {
      setCheckingLifecycle(false);
    }
  };

  const isLifecycleBlock = (error: unknown) => {
    const message = getApiErrorMessage(error, "The template action could not be completed.");
    return message.toLowerCase().includes("unfinished campaign") || message.toLowerCase().includes("used by campaigns");
  };

  const runAction = async (action: () => Promise<unknown>, success: string) => {
    setFeedback(null);
    try {
      await action();
      setFeedback({ tone: "success", text: success });
      showToast(success, "success");
    } catch (error) {
      setFeedback({ tone: "error", text: getApiErrorMessage(error, "The template action could not be completed.") });
    }
  };

  return (
    <PageContainer>
      <PageHeader
        title={template.name}
        description={template.description || "Reusable email template."}
        breadcrumbs={
          <div className="flex items-center gap-2">
            <Link
              to="/templates"
              className="inline-flex items-center gap-2 text-sm font-medium text-[#7A6208] hover:underline"
            >
              <ArrowLeft className="h-4 w-4" /> Back to Templates
            </Link>
            <span className="rounded-full border border-[#D8C990] bg-[#F8F0D7] px-3 py-1 text-xs font-semibold text-[#735E10]">
              {statusLabel(template.status)}
            </span>
          </div>
        }
        actions={
          <>
            {template.status === "published" ? (
              <button
                type="button"
                onClick={() => navigate({ to: "/templates" })}
                className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-[#735D0B]"
              >
                <ArrowLeft className="h-4 w-4" /> Continue to Templates
              </button>
            ) : null}
            {canEdit ? (
              <Link
                to="/templates/$templateUuid/edit"
                params={{ templateUuid }}
                className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white"
              >
                <Edit3 className="h-4 w-4" /> Edit
              </Link>
            ) : (
              <span className="inline-flex items-center gap-2 rounded-xl border border-[#DED7C7] bg-white px-4 py-2.5 text-sm font-semibold text-[#7B7464]">
                <Edit3 className="h-4 w-4" /> Edit (draft only)
              </span>
            )}
            {template.status === "draft" && (
              <button
                type="button"
                onClick={() =>
                  runAction(
                    () => publishMutation.mutateAsync(templateUuid),
                    "Template published successfully.",
                  )
                }
                className="inline-flex items-center gap-2 rounded-xl border border-[#D7C98F] bg-white px-4 py-2.5 text-sm font-semibold text-[#6E590A]"
              >
                <Send className="h-4 w-4" /> Publish
              </button>
            )}
            <button
              type="button"
              onClick={async () => {
                setFeedback(null);
                try {
                  const duplicated = await duplicateMutation.mutateAsync({
                    uuid: templateUuid,
                    name: `${template.name} Copy`,
                  });
                  setFeedback({ tone: "success", text: "Template duplicated as a draft." });
                  navigate({
                    to: "/templates/$templateUuid/edit",
                    params: { templateUuid: duplicated.uuid },
                  });
                } catch (error) {
                  setFeedback({
                    tone: "error",
                    text: getApiErrorMessage(
                      error,
                      "The template action could not be completed.",
                    ),
                  });
                }
              }}
              className="inline-flex items-center gap-2 rounded-xl border border-[#DED7C7] bg-white px-4 py-2.5 text-sm font-semibold text-[#554F41]"
            >
              <Copy className="h-4 w-4" /> Duplicate
            </button>
          </>
        }
      />

      {feedback && <div className="mt-5"><InlineNotice tone={feedback.tone}>{feedback.text}</InlineNotice></div>}

      <PageSection>
        <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="space-y-5">
          <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
              <FileText className="h-6 w-6" />
            </div>
            <dl className="mt-5 space-y-4 text-sm">
              <div><dt className="text-xs text-[#817966]">Subject</dt><dd className="mt-1 font-medium text-[#282D37]">{template.subject}</dd></div>
              <div><dt className="text-xs text-[#817966]">Category</dt><dd className="mt-1 font-medium text-[#282D37]">{category?.name || "Uncategorized"}</dd></div>
              <div><dt className="text-xs text-[#817966]">From</dt><dd className="mt-1 font-medium text-[#282D37]">{template.from_name || template.from_email || "Campaign sender"}</dd></div>
              <div><dt className="text-xs text-[#817966]">Last Updated</dt><dd className="mt-1 font-medium text-[#282D37]">{formatTemplateDate(template.updated_at || template.created_at)}</dd></div>
            </dl>
          </section>
          <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5">
            <h3 className="font-semibold text-[#171A22]">Template Actions</h3>
            {template.status === "published" && (
              <button
                type="button"
                onClick={() => prepareLifecycleAction("archive")}
                disabled={checkingLifecycle}
                className="mt-4 flex w-full items-center gap-2 rounded-xl border border-[#DED7C7] px-3.5 py-2.5 text-sm text-[#554F41] hover:bg-[#F8F5EC] disabled:cursor-wait disabled:opacity-50"
              >
                <Archive className="h-4 w-4" /> Archive Template
              </button>
            )}
            {template.status === "archived" && (
              <button
                type="button"
                onClick={() => setConfirmRestore(true)}
                className="mt-4 flex w-full items-center gap-2 rounded-xl border border-[#DED7C7] px-3.5 py-2.5 text-sm text-[#554F41] hover:bg-[#F8F5EC]"
              >
                <Edit3 className="h-4 w-4" /> Restore Template
              </button>
            )}
            <button
              type="button"
              onClick={() => prepareLifecycleAction("delete")}
              disabled={checkingLifecycle}
              className="mt-2 flex w-full items-center gap-2 rounded-xl border border-[#F0C8C5] px-3.5 py-2.5 text-sm text-[#B42318] hover:bg-[#FFF3F2] disabled:cursor-wait disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" /> Delete Template
            </button>
          </section>
        </aside>

        <section className="rounded-2xl border border-[#E8E1D0] bg-white p-5 sm:p-7">
          <div className="border-b border-[#EEE8DA] pb-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-[#8F740D]">Email Preview</p>
            <h2 className="mt-2 text-xl font-bold text-[#171A22]">{template.subject}</h2>
            {template.preheader && <p className="mt-1 text-sm text-[#817966]">{template.preheader}</p>}
          </div>
          <div className="mt-6 rounded-xl border border-[#E8E1D0] bg-[#FCFBF7] p-5 sm:p-8">
            <div className="rounded-xl bg-white px-6 py-7 shadow-sm">
              <p className="text-lg font-bold text-[#171A22]">MailTracko</p>
              {template.body_html ? (
                <EmailPreviewFrame
                  html={template.body_html}
                  title={`${template.name} preview`}
                  className="mt-5 min-h-[460px] rounded-lg"
                />
              ) : (
                <div className="mt-5">
                  <InlineNotice>
                    The current backend template-detail response does not include the saved HTML body,
                    so this preview will become available after that response contract is finalized.
                  </InlineNotice>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
      </PageSection>

      <Modal open={confirmArchive} title="Archive template?" description="Are you sure you want to archive this template? You can restore it later from Archived Templates." onClose={() => setConfirmArchive(false)}>
        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => setConfirmArchive(false)} className="rounded-xl border border-[#DED7C7] px-4 py-2.5 text-sm font-medium">Cancel</button>
          <button type="button" disabled={archiveMutation.isPending} onClick={async () => {
            try { await archiveMutation.mutateAsync(templateUuid); setConfirmArchive(false); setFeedback({ tone: "success", text: "Template archived successfully." }); }
            catch (error) { setConfirmArchive(false); if (isLifecycleBlock(error)) setBlockedLifecycle("archive"); else setFeedback({ tone: "error", text: getApiErrorMessage(error, "Template could not be archived.") }); }
          }} className="rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-55">Archive Template</button>
        </div>
      </Modal>

      <Modal open={confirmRestore} title="Unarchive template?" description="Are you sure you want to unarchive this template? It will return to your active templates as a draft." onClose={() => setConfirmRestore(false)}>
        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => setConfirmRestore(false)} className="rounded-xl border border-[#DED7C7] px-4 py-2.5 text-sm font-medium">Cancel</button>
          <button type="button" disabled={restoreMutation.isPending} onClick={async () => {
            try { await restoreMutation.mutateAsync(templateUuid); setConfirmRestore(false); setFeedback({ tone: "success", text: "Template restored successfully." }); }
            catch (error) { setConfirmRestore(false); setFeedback({ tone: "error", text: getApiErrorMessage(error, "Template could not be restored.") }); }
          }} className="rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-55">Unarchive Template</button>
        </div>
      </Modal>

      <Modal open={blockedLifecycle !== null} title="Template is being used by a campaign" description={`This template is currently being used by an unfinished campaign. You cannot ${blockedLifecycle ?? "change"} it until that campaign is finished.`} onClose={() => setBlockedLifecycle(null)}>
        <div className="flex justify-end"><button type="button" onClick={() => setBlockedLifecycle(null)} className="rounded-xl bg-[#1A1C1C] px-4 py-2.5 text-sm font-semibold text-white">OK</button></div>
      </Modal>

      <Modal open={confirmDelete} title="Delete template?" description="Are you sure you want to permanently delete this template? This action cannot be undone." onClose={() => setConfirmDelete(false)}>
        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => setConfirmDelete(false)} className="rounded-xl border border-[#DED7C7] px-4 py-2.5 text-sm font-medium">Cancel</button>
          <button type="button" disabled={deleteMutation.isPending} onClick={async () => {
            try { await deleteMutation.mutateAsync(templateUuid); navigate({ to: "/templates" }); }
            catch (error) { setConfirmDelete(false); if (isLifecycleBlock(error)) setBlockedLifecycle("delete"); else setFeedback({ tone: "error", text: getApiErrorMessage(error, "Template could not be deleted.") }); }
          }} className="rounded-xl bg-[#B42318] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-55">Delete Template</button>
        </div>
      </Modal>
    </PageContainer>
  );
};
