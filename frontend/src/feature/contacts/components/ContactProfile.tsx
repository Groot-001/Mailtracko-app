import { useMemo, useState, type SVGProps } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useSearch } from "@tanstack/react-router";
import { ArrowLeft, Edit2, Trash2, Mail, Layers, MousePointerClick, AlertTriangle, HelpCircle, Clock, ExternalLink, FileText, Loader2, CheckCircle2 } from "lucide-react";
import { useContactListDetail } from "../hooks/useContactLists";
import { useContacts } from "../hooks/useContacts";
import { useContactTimeline } from "../hooks/useContactTimeline";
import { AvatarInitials } from "../../organization/components/shared/AvatarInitials";
import { deleteContact, updateContact } from "../api/contactsApi";
import { getApiErrorMessage } from "../../../shared/utils/apiError";
import { ConfirmDialog } from "../../../shared/components/ConfirmDialog";

// ─── Timeline icons map ───────────────────────────────────────────────────────

const timelineIconsMap = {
  imported: FileText,
  merged: Layers,
  email_sent: Mail,
  email_opened: EyeIcon,
  email_clicked: MousePointerClick,
  bounced: AlertTriangle,
  unsubscribed: ShieldAlertIcon,
  manual_note: FileText,
};

function EyeIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function ShieldAlertIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

export const ContactProfile = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Record<string, string>>({});
  // TanStack Search parameters
  const search: { listUuid: string; contactUuid: string } = useSearch({
    from: "/_protected/contacts/profile",
  });

  const { data: listDetail } = useContactListDetail(search.listUuid);
  const { data: contactsData, isLoading: contactLoading } = useContacts(search.listUuid);
  const { data: timelineData, isLoading: timelineLoading } = useContactTimeline(
    search.listUuid,
    search.contactUuid
  );

  // Find exact contact inside list
  const contact = useMemo(() => {
    return contactsData?.items.find((c) => c.uuid === search.contactUuid) || null;
  }, [contactsData, search.contactUuid]);

  if (contactLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-[#8F740D] animate-spin" />
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="text-center py-20 text-[#4C4736]">
        <HelpCircle className="w-12 h-12 text-[#CEC6B0] mx-auto mb-3" />
        <p className="font-semibold text-sm">Contact not found</p>
        <Link to="/contacts" className="text-xs text-[#8F740D] underline mt-2 inline-block">
          Go back to contacts
        </Link>
      </div>
    );
  }

  const metadata = contact.metadata || {};
  const nameStr = `${metadata.first_name || ""} ${metadata.last_name || ""}`.trim() || contact.email;
  const tags = String(metadata.tags || "").split(",").map((tag) => tag.trim()).filter(Boolean);
  const standardFields = new Set(["first_name", "last_name", "name", "phone", "job_title", "company", "website", "location", "source", "tags"]);
  const customFields = Object.entries(metadata).filter(([key, value]) => !standardFields.has(key) && value !== null && value !== "");

  const openEdit = () => {
    setActionError(null);
    setEditForm({
      email: contact.email,
      first_name: metadata.first_name || "",
      last_name: metadata.last_name || "",
      phone: metadata.phone || "",
      job_title: metadata.job_title || "",
      company: metadata.company || "",
      website: metadata.website || "",
      location: metadata.location || "",
      source: metadata.source || "",
      tags: metadata.tags || "",
    });
    setIsEditing(true);
  };

  const saveEdit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setActionError(null);
    try {
      const nextMetadata = { ...metadata };
      for (const key of ["first_name", "last_name", "phone", "job_title", "company", "website", "location", "source", "tags"]) {
        nextMetadata[key] = editForm[key]?.trim() || null;
      }
      await updateContact(search.listUuid, contact.uuid, {
        email: editForm.email.trim(),
        metadata: nextMetadata,
      });
      await queryClient.invalidateQueries({ queryKey: ["contacts"] });
      setIsEditing(false);
    } catch (error: unknown) {
      setActionError(getApiErrorMessage(error, "Contact could not be updated."));
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    setActionError(null);
    setDeleting(true);
    try {
      await deleteContact(search.listUuid, contact.uuid);
      await queryClient.invalidateQueries({ queryKey: ["contacts"] });
      setDeleteOpen(false);
      await navigate({ to: "/contacts" });
    } catch (error: unknown) {
      setActionError(getApiErrorMessage(error, "Contact could not be deleted."));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="mx-auto max-w-[1480px] space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete contact?"
        description={`Delete ${contact.email}? This action cannot be undone.`}
        confirmLabel="Delete contact"
        isLoading={deleting}
        onConfirm={remove}
      />
      {/* Top back button */}
      <div>
        <Link
          to="/contacts"
          className="flex items-center gap-1 text-xs font-semibold text-[#4C4736] hover:text-[#8F740D]"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Contacts
        </Link>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6 items-start">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Main card metadata header */}
          <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 flex flex-col sm:flex-row gap-5 items-start sm:items-center">
            <AvatarInitials
              name={nameStr}
              email={contact.email}
              size="lg"
            />
            <div className="space-y-1.5 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl font-bold text-[#1A1C1C]">{nameStr}</h1>
                <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold ${contact.verification_status === "valid" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>
                  <CheckCircle2 className="w-3 h-3" /> {contact.verification_status?.replaceAll("_", " ") || "Unverified"}
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${contact.subscribed
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-orange-50 text-orange-700 border border-orange-200"
                    }`}
                >
                  {contact.status?.replaceAll("_", " ") || (contact.subscribed ? "Active" : "Unsubscribed")}
                </span>
              </div>
              <p className="text-xs text-[#4C4736]">
                {[metadata.job_title, metadata.company].filter(Boolean).join(" · ") || "No role or company provided"}
              </p>
              {/* Lists and tags lists */}
              <div className="flex flex-wrap gap-2 pt-1.5">
                <span className="bg-[#F1D442]/20 border border-[#F1D442]/50 text-[#8F740D] text-[10px] font-semibold px-2.5 py-0.5 rounded-full">
                  {listDetail?.name || "Collection unavailable"}
                </span>
                {tags.map((tag) => <span key={tag} className="bg-purple-50 border border-purple-200 text-purple-700 text-[10px] font-semibold px-2.5 py-0.5 rounded-full">{tag}</span>)}
              </div>
            </div>

            {/* Actions panel */}
            <div className="flex flex-col gap-2 w-full sm:w-auto shrink-0">
              <button type="button" onClick={openEdit} className="flex items-center justify-center gap-2 px-4 py-2 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-xs font-semibold rounded-xl">
                <Edit2 className="w-3.5 h-3.5" /> Edit Contact
              </button>
              <button type="button" onClick={() => setDeleteOpen(true)} className="flex items-center justify-center gap-2 px-4 py-2 bg-white border border-[#CEC6B0]/60 hover:bg-[#F4F3F3] text-red-600 text-xs font-semibold rounded-xl">
                <Trash2 className="w-3.5 h-3.5" /> Delete Contact
              </button>
            </div>
          </div>

          {actionError && <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800">{actionError}</p>}

          {/* Details strip */}
          <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-4">
            <h2 className="text-sm font-bold text-[#1A1C1C]">Contact Information</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-[#4C4736]">
              {[
                { label: "Full Name", value: nameStr },
                { label: "Email", value: contact.email, isMono: true },
                { label: "Phone", value: metadata.phone },
                { label: "Job Title", value: metadata.job_title },
                { label: "Company", value: metadata.company },
                { label: "Website", value: metadata.website, isLink: true },
                { label: "Location", value: metadata.location },
                { label: "Source", value: metadata.source },
              ].map((row, idx) => (
                <div key={idx} className="flex justify-between py-1.5 border-b border-[#F4F3F3]">
                  <span className="font-semibold text-[#1A1C1C]">{row.label}</span>
                  {row.isLink && row.value ? (
                    <a
                      href={row.value}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#8F740D] hover:underline flex items-center gap-1"
                    >
                      {row.value} <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className={row.isMono ? "font-mono" : ""}>{row.value || "Not provided"}</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Custom Fields section */}
          <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-sm font-bold text-[#1A1C1C]">Custom Fields</h2>
              <button type="button" onClick={openEdit} className="text-xs text-[#8F740D] font-bold hover:underline">Edit Fields</button>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {customFields.map(([key, value]) => (
                <div key={key} className="border border-[#CEC6B0]/40 rounded-xl p-3 bg-surface">
                  <p className="text-[10px] text-[#4C4736] uppercase font-bold">{key.replaceAll("_", " ")}</p>
                  <p className="text-xs font-semibold text-[#1A1C1C] mt-1">{value}</p>
                </div>
              ))}
              {customFields.length === 0 && <p className="col-span-full text-xs text-[#4C4736]">No custom fields have been added.</p>}
            </div>
          </div>
        </div>

        {/* Right Column: Timeline Log & Meta Info */}
        <div className="space-y-6">
          {/* Timeline Feed */}
          <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-4">
            <h2 className="text-sm font-bold text-[#1A1C1C]">Contact Timeline</h2>

            {timelineLoading ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="w-6 h-6 text-[#8F740D] animate-spin" />
              </div>
            ) : !timelineData || timelineData.items.length === 0 ? (
              <p className="text-xs text-[#4C4736]">No activities recorded yet.</p>
            ) : (
              <div className="relative pl-6 space-y-6 border-l border-[#EEEEEE]">
                {timelineData.items.map((item) => {
                  const IconComponent =
                    timelineIconsMap[item.activity_type as keyof typeof timelineIconsMap] || Clock;
                  return (
                    <div key={item.uuid} className="relative space-y-1">
                      {/* Node circle */}
                      <span className="absolute -left-9 top-0.5 w-6.5 h-6.5 bg-[#F4F3F3] border border-[#EEEEEE] rounded-full flex items-center justify-center">
                        <IconComponent className="w-3.5 h-3.5 text-[#8F740D]" />
                      </span>
                      <p className="text-xs font-bold text-[#1A1C1C]">{item.description}</p>
                      <p className="text-[10px] text-[#4C4736]">
                        {new Date(item.created_at).toLocaleString()}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Metadata info */}
          <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-5 space-y-3">
            <div className="text-xs space-y-2.5">
              <div className="flex justify-between">
                <span className="text-[#4C4736]">Contact ID</span>
                <span className="font-mono text-[#1A1C1C]">CT-{contact.uuid.slice(0, 8)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#4C4736]">Created At</span>
                <span className="text-[#1A1C1C]">{new Date(contact.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between"><span className="text-[#4C4736]">Verification score</span><span className="text-[#1A1C1C]">{contact.verification_score ?? "Not verified"}</span></div>
            </div>
          </div>
        </div>
      </div>

      {isEditing && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-[#1A1C1C]/45 p-4" role="dialog" aria-modal="true" aria-label="Edit contact">
          <form onSubmit={saveEdit} className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-[#CEC6B0] bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between gap-4"><div><h2 className="text-lg font-bold text-[#1A1C1C]">Edit contact</h2><p className="mt-1 text-xs text-[#4C4736]">Changes are saved to this contact and retained in its collection.</p></div><button type="button" onClick={() => setIsEditing(false)} className="rounded-lg border border-[#CEC6B0] px-3 py-1.5 text-xs font-semibold">Close</button></div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {[
                ["email", "Email"],
                ["first_name", "First name"],
                ["last_name", "Last name"],
                ["phone", "Phone"],
                ["job_title", "Job title"],
                ["company", "Company"],
                ["website", "Website"],
                ["location", "Location"],
                ["source", "Source"],
                ["tags", "Tags (comma separated)"],
              ].map(([key, label]) => <label key={key} className="block"><span className="text-xs font-bold text-[#4C4736]">{label}</span><input type={key === "email" ? "email" : "text"} required={key === "email"} value={editForm[key] || ""} onChange={(event) => setEditForm((current) => ({ ...current, [key]: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-[#CEC6B0]/60 px-3 py-2.5 text-sm outline-none focus:border-[#8F740D]" /></label>)}
            </div>
            {actionError && <p className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-800">{actionError}</p>}
            <div className="mt-6 flex justify-end gap-3 border-t border-[#F4F3F3] pt-4"><button type="button" onClick={() => setIsEditing(false)} className="rounded-xl border border-[#CEC6B0] px-4 py-2 text-xs font-bold">Cancel</button><button disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-4 py-2 text-xs font-bold text-white disabled:opacity-50">{saving && <Loader2 className="h-4 w-4 animate-spin" />} Save changes</button></div>
          </form>
        </div>
      )}
    </div>
  );
};
