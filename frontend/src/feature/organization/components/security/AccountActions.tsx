import { useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  Trash2,
  Users,
  Megaphone,
  BookUser,
  FileText,
  Plug,
  Paperclip,
  ShieldAlert,
  Building2,
} from "lucide-react";
import {
  useDeletionSummary,
  useOrganization,
  useRequestOrganizationDeletion,
} from "../../hooks/useOrganization";
import { Link } from "@tanstack/react-router";

// ─── Deletion impact items ────────────────────────────────────────────────────

const deletionItems = [
  {
    icon: Users,
    color: "bg-red-50 text-red-500",
    label: "All team members and their access",
    desc: "All member accounts and permissions will be removed.",
  },
  {
    icon: Megaphone,
    color: "bg-red-50 text-red-500",
    label: "All campaigns and sequences",
    desc: "All campaigns, drafts, schedules, and related data will be deleted.",
  },
  {
    icon: FileText,
    color: "bg-red-50 text-red-500",
    label: "All reports and analytics",
    desc: "All reports, analytics data, and performance history will be removed.",
  },
  {
    icon: BookUser,
    color: "bg-red-50 text-red-500",
    label: "All contacts and collections",
    desc: "All stored contacts, collections, and imported data will be permanently deleted.",
  },
  {
    icon: Plug,
    color: "bg-red-50 text-red-500",
    label: "All integrations and connections",
    desc: "All connected apps, API keys, and integration data will be revoked.",
  },
  {
    icon: Paperclip,
    color: "bg-red-50 text-red-500",
    label: "All files and attachments",
    desc: "All uploaded files, templates, and attachments will be removed.",
  },
];

// ─── Component ────────────────────────────────────────────────────────────────

export const AccountActions = () => {
  const { data: org } = useOrganization();
  const [confirmName, setConfirmName] = useState("");
  const [understood, setUnderstood] = useState(false);
  const orgName = org?.name ?? "Organization";
  const isConfirmValid =
    confirmName.trim().toLowerCase() === orgName.trim().toLowerCase() &&
    understood;

  const { data: summary } = useDeletionSummary();
  const deleteMutation = useRequestOrganizationDeletion();
  // Use the mutation state as the single source of truth.
  const isDeleting = deleteMutation.isPending;

  const handleDelete = async () => {
    if (!isConfirmValid) return;
    await deleteMutation.mutateAsync();
  };

  const handleCancelDeletion = () => {
    setConfirmName("");
    setUnderstood(false);
  };

  return (
    <div className="mx-auto max-w-[1480px] space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-[#1A1C1C] tracking-tight">
          Account Actions
        </h1>
        <h2 className="text-base font-semibold text-[#1A1C1C] mt-2">
          Delete organization
        </h2>
        <p className="text-sm text-[#4C4736] mt-1">
          Schedule deletion of your organization and all associated data. You can contact support during the grace period if deletion was requested by mistake.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6">
        {/* Left — Deletion form */}
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-6">
          {/* Warning banner */}
          <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4">
            <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-5 h-5 text-red-500" />
            </div>
            <div>
              <p className="text-sm font-bold text-red-700">
                This schedules organization deletion
              </p>
              <p className="text-xs text-red-600 mt-0.5 leading-relaxed">
                After the grace period, your organization data, settings, and member access will be removed.
              </p>
            </div>
          </div>

          {/* What will be deleted */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-[#1A1C1C]">
              What will be permanently deleted:
            </h3>
            <div className="space-y-3">
              {deletionItems.map((item) => (
                <div key={item.label} className="flex items-start gap-3">
                  <div className="flex items-center gap-2 flex-shrink-0 mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center ${item.color}`}
                    >
                      <item.icon className="w-3.5 h-3.5" />
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-[#1A1C1C]">
                      {item.label}
                    </p>
                    <p className="text-xs text-[#4C4736]">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Confirmation input */}
          <div className="space-y-3 border-t border-[#EEEEEE] pt-5">
            <div>
              <h3 className="text-sm font-bold text-[#1A1C1C]">
                Type the organization name to confirm
              </h3>
              <p className="text-xs text-[#4C4736] mt-0.5">
                Please type <strong>{orgName}</strong> exactly as shown to
                confirm deletion.
              </p>
            </div>

            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 rounded bg-[#F4F3F3] flex items-center justify-center">
                <Building2 className="w-3 h-3 text-[#8F740D]" />
              </div>
              <input
                id="confirm-org-name"
                type="text"
                value={confirmName}
                onChange={(e) => setConfirmName(e.target.value)}
                placeholder={orgName}
                className={`w-full pl-10 pr-3 py-2.5 rounded-xl border text-sm text-[#1A1C1C] placeholder:text-red-300 focus:outline-none focus:ring-2 transition-all ${
                  confirmName &&
                  confirmName.trim().toLowerCase() !==
                    orgName.trim().toLowerCase()
                    ? "border-red-400 focus:ring-red-200"
                    : "border-[#CEC6B0]/60 focus:ring-[#F1D442]/50 focus:border-[#8F740D]"
                }`}
              />
            </div>
            {confirmName &&
              confirmName.trim().toLowerCase() !==
                orgName.trim().toLowerCase() && (
                <p className="text-xs text-red-500">This field is required.</p>
              )}

            {/* Checkbox */}
            <label className="flex items-start gap-3 cursor-pointer group">
              <input
                id="confirm-understand"
                type="checkbox"
                checked={understood}
                onChange={(e) => setUnderstood(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded border-[#CEC6B0] text-[#8F740D] focus:ring-[#F1D442]/50 accent-[#8F740D]"
              />
              <div>
                <p className="text-sm font-medium text-[#1A1C1C]">
                  I understand that this action is permanent and all data will
                  be lost forever.
                </p>
                <p className="text-xs text-[#4C4736]">
                  There is no way to recover any data after deletion.
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Right — Data summary */}
        <div className="space-y-6">
          <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-4">
            <div>
              <h2 className="text-base font-semibold text-[#1A1C1C]">
                Data summary
              </h2>
              <p className="text-xs text-[#4C4736] mt-0.5">
                The following data will be permanently deleted and cannot be
                recovered.
              </p>
              {summary ? (
                <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">
                  Final deletion is scheduled after a {summary.grace_period_days}-day grace period.
                </p>
              ) : null}
            </div>

            <div className="space-y-4">
              {[
                {
                  icon: Users,
                  color: "bg-red-50 text-red-500",
                  value: summary?.data_summary.team_members ?? 0,
                  label: "Team members",
                  desc: "All member accounts and access",
                },
                {
                  icon: Megaphone,
                  color: "bg-orange-50 text-orange-500",
                  value: summary?.data_summary.campaigns ?? 0,
                  label: "Campaigns",
                  desc: "All campaigns and sequences",
                },
                {
                  icon: BookUser,
                  color: "bg-blue-50 text-blue-600",
                  value: summary?.data_summary.stored_contacts ?? 0,
                  label: "Stored contacts",
                  desc: "All contacts and collections",
                },
                {
                  icon: FileText,
                  color: "bg-purple-50 text-purple-600",
                  value: summary?.data_summary.files_and_attachments ?? 0,
                  label: "Files and attachments",
                  desc: "Uploaded files and email templates",
                },
              ].map((stat) => (
                <div key={stat.label} className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${stat.color}`}
                  >
                    <stat.icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xl font-bold text-[#1A1C1C]">
                      {stat.value}
                    </p>
                    <p className="text-xs font-semibold text-[#1A1C1C]">
                      {stat.label}
                    </p>
                    <p className="text-[10px] text-[#4C4736]">{stat.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-xl px-3 py-2.5 mt-2">
              <ShieldAlert className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-red-700">
                  Deletion uses a grace period
                </p>
                <p className="text-[10px] text-red-600">
                  The request is scheduled before final cleanup. Verify the request carefully and contact support before the grace period ends if it was accidental.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sticky footer */}
      <div className="sticky bottom-0 bg-white border-t border-[#EEEEEE] -mx-6 lg:-mx-8 px-6 lg:px-8 py-4 flex items-center justify-start gap-3">
        <button
          type="button"
          onClick={handleCancelDeletion}
          disabled={isDeleting}
          className="px-5 py-2.5 rounded-xl border border-[#CEC6B0]/60 text-sm font-medium text-[#1A1C1C] hover:bg-[#F4F3F3] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel deletion
        </button>
        <Link
          to="/organization"
          className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl border border-[#CEC6B0]/60 text-sm font-medium text-[#1A1C1C] hover:bg-[#F4F3F3] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Go back
        </Link>
        <button
          id="delete-org-btn"
          onClick={handleDelete}
          disabled={!isConfirmValid || isDeleting}
          className="flex items-center gap-2 px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Trash2 className="w-4 h-4" />
          {isDeleting ? "Scheduling…" : `Schedule deletion for ${orgName}`}
        </button>
      </div>
    </div>
  );
};
