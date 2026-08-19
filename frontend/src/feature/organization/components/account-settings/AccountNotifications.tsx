import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Loader2, Mail, Save } from "lucide-react";

import {
  getNotificationPreferences,
  saveNotificationPreferences,
  type NotificationPreferences,
} from "../../../platform/api/platformApi";
import { ToggleSwitch } from "../shared/ToggleSwitch";

const categories = [
  ["campaign_activity", "Campaign activity", "Launches, pauses, completions, and delivery warnings."],
  ["engagement", "Recipient engagement", "Opens, clicks, replies, and tracked conversations."],
  ["deliverability", "Deliverability", "Bounces, provider health, limits, and suppression events."],
  ["security", "Security", "Suspicious sign-ins and sensitive account changes."],
  ["billing", "Billing", "Invoices, payment failures, plan, and subscription changes."],
  ["product_updates", "Product updates", "Important product and service announcements."],
] as const;

const defaults: NotificationPreferences = {
  email_enabled: true,
  in_app_enabled: true,
  categories: Object.fromEntries(categories.map(([key]) => [key, true])),
};

export const AccountNotifications = () => {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["platform", "preferences"], queryFn: getNotificationPreferences });
  const [localOverride, setLocalOverride] = useState<NotificationPreferences | null>(null);
  const [saved, setSaved] = useState(false);

  const sourceForm = useMemo<NotificationPreferences>(() => {
    if (!query.data) return defaults;

    return {
      ...defaults,
      ...query.data,
      categories: {
        ...defaults.categories,
        ...query.data.categories,
      },
    };
  }, [query.data]);

  const form = localOverride ?? sourceForm;

  const updateForm = (updates: Partial<NotificationPreferences> | ((current: NotificationPreferences) => Partial<NotificationPreferences>)) => {
    const currentBase = form;
    const nextValue = typeof updates === "function"
      ? { ...currentBase, ...updates(currentBase) }
      : { ...currentBase, ...updates };

    setSaved(false);
    setLocalOverride(nextValue);
  };

  const mutation = useMutation({
    mutationFn: saveNotificationPreferences,
    onSuccess: (value) => {
      setSaved(true);
      setLocalOverride(null);
      queryClient.setQueryData(["platform", "preferences"], value);
    },
  });

  if (query.isLoading) return <div className="grid min-h-60 place-items-center"><Loader2 className="h-5 w-5 animate-spin text-[#8F740D]" /></div>;

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
        <div><h2 className="font-bold text-[#1A1C1C]">Notification channels</h2><p className="mt-1 text-xs text-[#756F60]">Control where enabled categories can reach you.</p></div>
        <div className="mt-5 divide-y divide-[#F4F1E8]">
          <div className="flex items-center justify-between py-4"><div className="flex gap-3"><Mail className="h-5 w-5 text-[#8F740D]" /><div><p className="text-sm font-semibold">Email notifications</p><p className="text-xs text-[#756F60]">Receive messages at your verified account email.</p></div></div><ToggleSwitch id="email-enabled" checked={form.email_enabled} onChange={(value) => { updateForm((current) => ({ ...current, email_enabled: value })); }} /></div>
          <div className="flex items-center justify-between py-4"><div className="flex gap-3"><Bell className="h-5 w-5 text-[#8F740D]" /><div><p className="text-sm font-semibold">In-app notifications</p><p className="text-xs text-[#756F60]">Show notifications in the MailTracko workspace.</p></div></div><ToggleSwitch id="in-app-enabled" checked={form.in_app_enabled} onChange={(value) => { updateForm((current) => ({ ...current, in_app_enabled: value })); }} /></div>
        </div>
      </section>

      <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
        <div><h2 className="font-bold text-[#1A1C1C]">Categories</h2><p className="mt-1 text-xs text-[#756F60]">Critical transactional and legal messages may still be delivered.</p></div>
        <div className="mt-5 divide-y divide-[#F4F1E8]">
          {categories.map(([key, label, description]) => (
            <div key={key} className="flex items-center justify-between gap-5 py-4"><div><p className="text-sm font-semibold text-[#1A1C1C]">{label}</p><p className="mt-0.5 text-xs text-[#756F60]">{description}</p></div><ToggleSwitch id={`category-${key}`} checked={form.categories[key] ?? true} onChange={(value) => { updateForm((current) => ({ ...current, categories: { ...current.categories, [key]: value } })); }} /></div>
          ))}
        </div>
      </section>

      {query.isError && <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">Saved notification preferences could not be loaded.</p>}
      {mutation.isError && <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">Your preferences could not be saved.</p>}
      {saved && <p className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">Notification preferences saved.</p>}
      <div className="flex justify-end"><button type="button" disabled={mutation.isPending} onClick={() => mutation.mutate(form)} className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-5 py-2.5 text-sm font-bold text-white disabled:opacity-50">{mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Save preferences</button></div>
    </div>
  );
};
