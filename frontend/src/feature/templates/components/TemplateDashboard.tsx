import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  Archive,
  CheckCircle2,
  Copy,
  Edit3,
  Eye,
  FileText,
  Folder,
  MoreVertical,
  Plus,
  Search,
  Send,
  Trash2,
} from "lucide-react";
import { AppSelect } from "../../../shared/components/AppSelect";
import { PaginationControls } from "../../../shared/components/PaginationControls";
import { InlineNotice } from "../../../shared/components/InlineNotice";
import { Modal } from "../../../shared/components/Modal";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { PageContainer, PageHeader, PageSection } from "../../../shared/components/layout";
import {
  useArchiveTemplate,
  useDeleteTemplate,
  useDuplicateTemplate,
  usePublishTemplate,
  useRestoreTemplate,
  useTemplateCategories,
  useTemplateSummary,
  useTemplates,
} from "../hooks/useTemplates";
import type { EmailTemplate, TemplateStatus } from "../types/template.types";
import { formatTemplateDate, statusLabel } from "../utils/templateFormatters";
import { getTemplateCampaignUsage } from "../api/templateApi";


const SummaryCard = ({
  icon: Icon,
  label,
  value,
  description,
}: {
  icon: typeof FileText;
  label: string;
  value: number;
  description: string;
}) => (
  <div className="rounded-2xl border border-[#E8E1D0] bg-white p-5 shadow-[0_8px_24px_rgba(66,54,16,0.04)]">
    <div className="flex items-center gap-4">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#F8F0D7] text-[#8F740D]">
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm text-[#696253]">{label}</p>
        <p className="mt-0.5 text-2xl font-bold text-[#111827]">{value}</p>
        <p className="mt-1 text-xs text-[#99917D]">{description}</p>
      </div>
    </div>
  </div>
);

const TemplateStatusBadge = ({ status }: { status: string }) => {
  const styles =
    status === "published"
      ? "bg-[#EAF7ED] text-[#26733D] border-[#CDE8D4]"
      : status === "archived"
        ? "bg-[#F1F1F1] text-[#5F6470] border-[#DEDEDE]"
        : "bg-[#FFF4DB] text-[#976312] border-[#F0D9A6]";
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${styles}`}>
      {statusLabel(status)}
    </span>
  );
};

export const TemplateDashboard = () => {
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<TemplateStatus | "">("");
  const [section, setSection] = useState<"active" | "archived">("active");
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{ top?: number; bottom?: number; right: number } | null>(null);
  const actionMenuRef = useRef<HTMLDivElement | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<EmailTemplate | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<EmailTemplate | null>(null);
  const [restoreTarget, setRestoreTarget] = useState<EmailTemplate | null>(null);
  const [blockedLifecycle, setBlockedLifecycle] = useState<{ template: EmailTemplate; operation: "archive" | "delete" } | null>(null);
  const [checkingLifecycleUuid, setCheckingLifecycleUuid] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ tone: "success" | "error"; text: string } | null>(
    null,
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 250);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const params = useMemo(
    () => ({
      search,
      status: section === "archived" ? "archived" as const : status,
      include_archived: section === "archived",
      category_id: categoryId,
      limit: pageSize,
      offset: (page - 1) * pageSize,
    }),
    [categoryId, page, pageSize, search, section, status],
  );

  const templatesQuery = useTemplates(params);
  const summaryQuery = useTemplateSummary();
  const categoriesQuery = useTemplateCategories();
  const duplicateMutation = useDuplicateTemplate();
  const publishMutation = usePublishTemplate();
  const archiveMutation = useArchiveTemplate();
  const restoreMutation = useRestoreTemplate();
  const deleteMutation = useDeleteTemplate();
  useEffect(() => {
    if (!openMenu) return;

    const closeOnOutsideClick = (event: MouseEvent) => {
      const target = event.target as Element | null;
      if (target?.closest("[data-action-menu-trigger='true']")) return;
      if (!actionMenuRef.current?.contains(target as Node)) {
        setOpenMenu(null);
      }
    };

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpenMenu(null);
      }
    };

    const closeOnViewportChange = () => setOpenMenu(null);
    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    window.addEventListener("resize", closeOnViewportChange);
    window.addEventListener("scroll", closeOnViewportChange, true);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
      window.removeEventListener("resize", closeOnViewportChange);
      window.removeEventListener("scroll", closeOnViewportChange, true);
    };
  }, [openMenu]);


  const totalPages = Math.max(1, Math.ceil((templatesQuery.data?.total ?? 0) / pageSize));
  const summary = summaryQuery.data;

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const resetFilters = () => {
    setSearchInput("");
    setSearch("");
    setStatus("");
    setCategoryId(undefined);
    setPage(1);
  };

  const switchSection = (next: "active" | "archived") => {
    setSection(next);
    setStatus("");
    setPage(1);
    setOpenMenu(null);
  };

  const handleDuplicate = async (template: EmailTemplate) => {
    try {
      const duplicated = await duplicateMutation.mutateAsync({ uuid: template.uuid, name: `${template.name} Copy` });
      setFeedback({ tone: "success", text: "Template duplicated as a new draft." });
      navigate({ to: "/templates/$templateUuid/edit", params: { templateUuid: duplicated.uuid } });
    } catch (error) {
      setFeedback({ tone: "error", text: getApiErrorMessage(error, "Unable to duplicate template.") });
    } finally {
      setOpenMenu(null);
    }
  };

  const handlePublish = async (template: EmailTemplate) => {
    try {
      await publishMutation.mutateAsync(template.uuid);
      setFeedback({ tone: "success", text: "Template published successfully." });
    } catch (error) {
      setFeedback({ tone: "error", text: getApiErrorMessage(error, "Unable to publish template.") });
    } finally {
      setOpenMenu(null);
    }
  };

  const prepareLifecycleAction = async (template: EmailTemplate, operation: "archive" | "delete") => {
    setOpenMenu(null);
    setFeedback(null);
    setCheckingLifecycleUuid(template.uuid);
    try {
      const usage = await getTemplateCampaignUsage(template.uuid);
      if (usage.in_use) {
        setBlockedLifecycle({ template, operation });
        return;
      }
      if (operation === "archive") setArchiveTarget(template);
      else setDeleteTarget(template);
    } catch (error) {
      setFeedback({ tone: "error", text: getApiErrorMessage(error, "Unable to check whether this template is used by a campaign.") });
    } finally {
      setCheckingLifecycleUuid(null);
    }
  };

  const surfaceLifecycleBlock = (template: EmailTemplate, operation: "archive" | "delete", error: unknown) => {
    const message = getApiErrorMessage(error, `Unable to ${operation} template.`);
    if (message.toLowerCase().includes("unfinished campaign") || message.toLowerCase().includes("used by campaigns")) {
      setArchiveTarget(null);
      setDeleteTarget(null);
      setBlockedLifecycle({ template, operation });
      return true;
    }
    setFeedback({ tone: "error", text: message });
    return false;
  };

  const handleArchive = async (template: EmailTemplate) => {
    try {
      await archiveMutation.mutateAsync(template.uuid);
      setFeedback({ tone: "success", text: "Template archived successfully." });
      setArchiveTarget(null);
    } catch (error) {
      surfaceLifecycleBlock(template, "archive", error);
    } finally {
      setOpenMenu(null);
    }
  };

  const handleRestore = async (template: EmailTemplate) => {
    try {
      await restoreMutation.mutateAsync(template.uuid);
      setFeedback({ tone: "success", text: "Template restored successfully." });
      setRestoreTarget(null);
    } catch (error) {
      setFeedback({ tone: "error", text: getApiErrorMessage(error, "Unable to restore template.") });
    } finally {
      setOpenMenu(null);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteMutation.mutateAsync(deleteTarget.uuid);
      setFeedback({ tone: "success", text: "Template deleted successfully." });
      setDeleteTarget(null);
    } catch (error) {
      surfaceLifecycleBlock(deleteTarget, "delete", error);
    }
  };

  return (
    <PageContainer>
      <PageHeader
        title="Templates"
        description="Create, manage, and reuse email templates across your campaigns."
        actions={
          <Link
            to="/templates/new"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-5 py-3 text-sm font-semibold text-white shadow-button transition-colors hover:bg-[#735D0B]"
          >
            <Plus className="h-4 w-4" />
            New Template
          </Link>
        }
      />

      {feedback && (
        <div className="mt-5">
          <InlineNotice tone={feedback.tone}>{feedback.text}</InlineNotice>
        </div>
      )}

      <PageSection>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <SummaryCard
            icon={FileText}
            label="Total Templates"
            value={summary?.total_templates ?? 0}
            description="All organization templates"
          />
          <SummaryCard
            icon={CheckCircle2}
            label="Published"
            value={summary?.published_templates ?? 0}
            description="Ready for campaigns"
          />
          <SummaryCard
            icon={Edit3}
            label="Drafts"
            value={summary?.draft_templates ?? 0}
            description="Still being prepared"
          />
          <SummaryCard
            icon={Folder}
            label="Categories"
            value={summary?.total_categories ?? 0}
            description="Available template categories"
          />
        </div>
      </PageSection>

      <PageSection>
        <div className="inline-flex rounded-xl border border-[#DED7C7] bg-white p-1">
        <button
          type="button"
          onClick={() => switchSection("active")}
          className={`rounded-lg px-4 py-2 text-sm font-semibold ${section === "active" ? "bg-[#8F740D] text-white" : "text-[#625A47] hover:bg-[#F8F5EC]"}`}
        >
          Active Templates
        </button>
        <button
          type="button"
          onClick={() => switchSection("archived")}
          className={`rounded-lg px-4 py-2 text-sm font-semibold ${section === "archived" ? "bg-[#8F740D] text-white" : "text-[#625A47] hover:bg-[#F8F5EC]"}`}
        >
          Archived Templates ({summary?.archived_templates ?? 0})
        </button>
      </div>

      <section className="mt-4 overflow-visible rounded-2xl border border-[#E8E1D0] bg-white shadow-[0_8px_28px_rgba(66,54,16,0.04)]">
        <div className="grid gap-3 border-b border-[#EEE8DA] p-4 md:grid-cols-[minmax(240px,1fr)_200px_190px_auto]">
          <label className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8D8572]" />
            <input
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search templates by name or subject..."
              className="h-11 w-full rounded-xl border border-[#DED7C7] bg-white pl-10 pr-3 text-sm outline-none transition focus:border-[#A88916] focus:ring-1 focus:ring-[#E9DFAE]/60"
            />
          </label>
          <AppSelect value={categoryId?.toString() ?? ""} onValueChange={(value) => { setCategoryId(value ? Number(value) : undefined); setPage(1); }} ariaLabel="Filter templates by category" searchable options={[{ value: "", label: "All Categories" }, ...(categoriesQuery.data?.map((category) => ({ value: category.id.toString(), label: category.name })) ?? [])]} />
          {section === "active" ? (
            <AppSelect value={status} onValueChange={(value) => { setStatus(value as TemplateStatus | ""); setPage(1); }} ariaLabel="Template status" options={[{ value: "", label: "All Active Statuses" }, { value: "published", label: "Published" }, { value: "draft", label: "Draft" }]} />
          ) : (
            <div className="flex h-11 items-center rounded-xl border border-[#DED7C7] bg-[#F8F5EC] px-3 text-sm font-medium text-[#625A47]">Archived only</div>
          )}
          <button
            type="button"
            onClick={resetFilters}
            className="h-11 rounded-xl border border-[#DED7C7] px-4 text-sm font-medium text-[#625A47] hover:bg-[#F8F5EC]"
          >
            Clear Filters
          </button>
        </div>

        {templatesQuery.isError ? (
          <div className="p-6">
            <InlineNotice tone="error">
              {getApiErrorMessage(templatesQuery.error, "Templates could not be loaded.")}
            </InlineNotice>
          </div>
        ) : templatesQuery.isLoading && !templatesQuery.data ? (
          <div className="space-y-3 p-5">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="h-16 animate-pulse rounded-xl bg-[#F5F2EA]" />
            ))}
          </div>
        ) : templatesQuery.data?.items.length ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[920px] border-collapse">
                <thead>
                  <tr className="border-b border-[#EEE8DA] bg-[#FCFBF7] text-left text-xs font-semibold text-[#6E6757]">
                    <th className="px-5 py-3.5">Template</th>
                    <th className="px-4 py-3.5">Category</th>
                    <th className="px-4 py-3.5">Subject</th>
                    <th className="px-4 py-3.5">Last Updated</th>
                    <th className="px-4 py-3.5">Status</th>
                    <th className="w-24 px-4 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {templatesQuery.data.items.map((template) => {
                    const category = categoriesQuery.data?.find(
                      (item) => item.id === template.category_id,
                    );
                    return (
                      <tr key={template.uuid} className="border-b border-[#F0ECE2] last:border-0 hover:bg-[#FFFDF8]">
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#F8F0D7] text-[#8F740D]">
                              <Send className="h-5 w-5" />
                            </div>
                            <div>
                              <button
                                type="button"
                                onClick={() => navigate({ to: "/templates/$templateUuid", params: { templateUuid: template.uuid } })}
                                className="text-left text-sm font-semibold text-[#171A22] hover:text-[#8F740D]"
                              >
                                {template.name}
                              </button>
                              <p className="mt-0.5 text-[11px] text-[#98907D]">{template.template_type}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <span className="rounded-lg bg-[#F7F0DA] px-2.5 py-1 text-xs text-[#735E10]">
                            {category?.name ?? "Uncategorized"}
                          </span>
                        </td>
                        <td className="max-w-[260px] truncate px-4 py-4 text-sm text-[#4C5365]">
                          {template.subject}
                        </td>
                        <td className="px-4 py-4 text-xs leading-5 text-[#5E6471]">
                          {formatTemplateDate(template.updated_at || template.created_at)}
                        </td>
                        <td className="px-4 py-4">
                          <TemplateStatusBadge status={template.status} />
                        </td>
                        <td className="w-24 px-4 py-4 text-right">
                          <div className="relative inline-flex items-center justify-end">
                            <button
                              type="button"
                              onClick={(event) => {
                                if (openMenu === template.uuid) {
                                  setOpenMenu(null);
                                  return;
                                }
                                const rect = event.currentTarget.getBoundingClientRect();
                                const estimatedMenuHeight = 280;
                                const openUpward =
                                  window.innerHeight - rect.bottom < estimatedMenuHeight &&
                                  rect.top > estimatedMenuHeight;
                                setMenuPosition({
                                  ...(openUpward
                                    ? { bottom: Math.max(8, window.innerHeight - rect.top + 6) }
                                    : { top: rect.bottom + 6 }),
                                  right: Math.max(8, window.innerWidth - rect.right),
                                });
                                setOpenMenu(template.uuid);
                              }}
                              data-action-menu-trigger="true"
                              className="rounded-lg p-2 text-[#5F6470] hover:bg-[#F2EEE4]"
                              aria-label={`Actions for ${template.name}`}
                            >
                              <MoreVertical className="h-4 w-4" />
                            </button>
                            {openMenu === template.uuid && (
                              <div
                                ref={actionMenuRef}
                                style={menuPosition ?? undefined}
                                className="fixed z-50 w-48 rounded-xl border border-[#E4DDCD] bg-white p-1.5 text-left shadow-xl"
                              >
                                <Link
                                  to="/templates/$templateUuid"
                                  params={{ templateUuid: template.uuid }}
                                  onClick={() => setOpenMenu(null)}
                                  className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
                                >
                                  <Eye className="h-4 w-4" /> Preview
                                </Link>
                                {template.status === "draft" ? (
                                  <Link
                                    to="/templates/$templateUuid/edit"
                                    params={{ templateUuid: template.uuid }}
                                    onClick={() => setOpenMenu(null)}
                                    className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
                                  >
                                    <Edit3 className="h-4 w-4" /> Edit
                                  </Link>
                                ) : (
                                  <span className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#9A9487]">
                                    <Edit3 className="h-4 w-4" /> Edit (draft only)
                                  </span>
                                )}
                                {template.status === "draft" && (
                                  <button
                                    type="button"
                                    onClick={() => handlePublish(template)}
                                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
                                  >
                                    <Send className="h-4 w-4" /> Publish
                                  </button>
                                )}
                                <button
                                  type="button"
                                  onClick={() => handleDuplicate(template)}
                                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
                                >
                                  <Copy className="h-4 w-4" /> Duplicate
                                </button>
                                {template.status === "published" && (
                                  <button
                                    type="button"
                                    onClick={() => prepareLifecycleAction(template, "archive")}
                                    disabled={checkingLifecycleUuid === template.uuid}
                                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9] disabled:cursor-wait disabled:opacity-50"
                                  >
                                    <Archive className="h-4 w-4" /> Archive
                                  </button>
                                )}
                                {template.status === "archived" && (
                                  <button
                                    type="button"
                                    onClick={() => { setRestoreTarget(template); setOpenMenu(null); }}
                                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#3E4350] hover:bg-[#F8F4E9]"
                                  >
                                    <CheckCircle2 className="h-4 w-4" /> Restore
                                  </button>
                                )}
                                <button
                                  type="button"
                                  onClick={() => prepareLifecycleAction(template, "delete")}
                                  disabled={checkingLifecycleUuid === template.uuid}
                                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-[#B42318] hover:bg-[#FFF1EF] disabled:cursor-wait disabled:opacity-50"
                                >
                                  <Trash2 className="h-4 w-4" /> Delete
                                </button>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <PaginationControls
              page={page}
              pageSize={pageSize}
              total={templatesQuery.data.total}
              itemLabel="templates"
              onPageChange={setPage}
              onPageSizeChange={(value) => { setPageSize(value); setPage(1); }}
              isLoading={templatesQuery.isFetching}
              className="border-t border-[#EEE8DA] px-5 py-4"
            />
          </>
        ) : (
          <div className="px-6 py-16 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#F8F0D7] text-[#8F740D]">
              <FileText className="h-7 w-7" />
            </div>
            <h2 className="mt-4 text-lg font-semibold text-[#111827]">{section === "archived" ? "No archived templates" : "No templates found"}</h2>
            <p className="mx-auto mt-1 max-w-md text-sm text-[#756E5C]">
              {section === "archived" ? "Templates you archive will appear here and can be restored or permanently deleted." : "Create a new template or clear the filters to see your existing templates."}
            </p>
            {section === "active" && (
              <Link
                to="/templates/new"
                className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white"
              >
                <Plus className="h-4 w-4" /> New Template
              </Link>
            )}
          </div>
        )}
      </section>
    </PageSection>

      <Modal
        open={Boolean(archiveTarget)}
        title="Archive template?"
        description={`Are you sure you want to archive ${archiveTarget?.name ?? "this template"}? You can restore it later from Archived Templates.`}
        onClose={() => setArchiveTarget(null)}
      >
        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => setArchiveTarget(null)} className="rounded-xl border border-[#DED7C7] px-4 py-2.5 text-sm font-medium text-[#514B3C]">Cancel</button>
          <button type="button" onClick={() => archiveTarget && handleArchive(archiveTarget)} disabled={archiveMutation.isPending} className="rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60">
            {archiveMutation.isPending ? "Archiving..." : "Archive Template"}
          </button>
        </div>
      </Modal>

      <Modal
        open={Boolean(restoreTarget)}
        title="Unarchive template?"
        description={`Are you sure you want to unarchive ${restoreTarget?.name ?? "this template"}? It will return to your active templates as a draft.`}
        onClose={() => setRestoreTarget(null)}
      >
        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => setRestoreTarget(null)} className="rounded-xl border border-[#DED7C7] px-4 py-2.5 text-sm font-medium text-[#514B3C]">Cancel</button>
          <button type="button" onClick={() => restoreTarget && handleRestore(restoreTarget)} disabled={restoreMutation.isPending} className="rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60">
            {restoreMutation.isPending ? "Unarchiving..." : "Unarchive Template"}
          </button>
        </div>
      </Modal>

      <Modal
        open={Boolean(blockedLifecycle)}
        title="Template is being used by a campaign"
        description={`This template is currently being used by an unfinished campaign. You cannot ${blockedLifecycle?.operation ?? "change"} it until that campaign is finished.`}
        onClose={() => setBlockedLifecycle(null)}
      >
        <div className="flex justify-end">
          <button type="button" onClick={() => setBlockedLifecycle(null)} className="rounded-xl bg-[#1A1C1C] px-4 py-2.5 text-sm font-semibold text-white">OK</button>
        </div>
      </Modal>

      <Modal
        open={Boolean(deleteTarget)}
        title="Delete template?"
        description="This permanently removes the selected template. This action cannot be undone."
        onClose={() => setDeleteTarget(null)}
      >
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => setDeleteTarget(null)}
            className="rounded-xl border border-[#DED7C7] px-4 py-2.5 text-sm font-medium text-[#514B3C]"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={confirmDelete}
            disabled={deleteMutation.isPending}
            className="rounded-xl bg-[#B42318] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete Template"}
          </button>
        </div>
      </Modal>
    </PageContainer>
  );
};
