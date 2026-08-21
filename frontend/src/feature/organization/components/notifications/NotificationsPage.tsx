import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Building2, CheckCheck, Loader2, MailOpen, ShieldCheck } from "lucide-react";
import { PageContainer, PageHeader, PageSection } from "../../../../shared/components/layout";

import {
  getAppNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../../../platform/api/platformApi";
import { listRecentActivities } from "../../api/organizationApi";
import { listUserActivities } from "../../../../shared/api/authApi";

const formatDate = (value: string) =>
  new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );

const label = (value: string) => value.replaceAll("_", " ");

type NotificationView = "personal" | "organization" | "system";

export const NotificationsPage = () => {
  const queryClient = useQueryClient();
  const [view, setView] = useState<NotificationView>("personal");
  const [unreadOnly, setUnreadOnly] = useState(false);

  const personal = useQuery({
    queryKey: ["auth", "activities", 100],
    queryFn: () => listUserActivities(100, 0),
    enabled: view === "personal",
    refetchInterval: view === "personal" ? 30_000 : false,
    refetchIntervalInBackground: false,
  });
  const organization = useQuery({
    queryKey: ["organization", "activities", { limit: 100, offset: 0 }],
    queryFn: () => listRecentActivities({ limit: 100, offset: 0 }),
    enabled: view === "organization",
    refetchInterval: view === "organization" ? 30_000 : false,
    refetchIntervalInBackground: false,
  });
  const system = useQuery({
    queryKey: ["platform", "notifications", unreadOnly],
    queryFn: () => getAppNotifications(unreadOnly),
    enabled: view === "system",
    refetchInterval: view === "system" ? 30_000 : false,
    refetchIntervalInBackground: false,
  });

  const refreshSystem = () => queryClient.invalidateQueries({ queryKey: ["platform", "notifications"] });
  const read = useMutation({ mutationFn: markNotificationRead, onSuccess: refreshSystem });
  const readAll = useMutation({ mutationFn: markAllNotificationsRead, onSuccess: refreshSystem });

  const tabClass = (tab: NotificationView) =>
    `inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-bold transition ${
      view === tab ? "bg-[#1A1C1C] text-white" : "border border-[#CEC6B0]/60 bg-white text-[#514A38] hover:bg-[#F8F4E9]"
    }`;

  return (
    <PageContainer nested>
      <PageHeader
        title="Notifications"
        description="Personal account activity is kept separate from organization/team activity and system notifications."
        breadcrumbs={
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#8F740D]">
            Activity center
          </p>
        }
        actions={
          <div className="flex flex-wrap gap-2" role="tablist" aria-label="Notification type">
            <button
              type="button"
              className={tabClass("personal")}
              onClick={() => setView("personal")}
            >
              <ShieldCheck className="h-4 w-4" /> Personal
            </button>
            <button
              type="button"
              className={tabClass("organization")}
              onClick={() => setView("organization")}
            >
              <Building2 className="h-4 w-4" /> Organization
            </button>
            <button
              type="button"
              className={tabClass("system")}
              onClick={() => setView("system")}
            >
              <Bell className="h-4 w-4" /> System
            </button>
          </div>
        }
      />
      <PageSection>

      {view === "system" && (
        <div className="flex flex-wrap justify-end gap-2">
          <button
            type="button"
            onClick={() => setUnreadOnly((current) => !current)}
            className={`rounded-xl border px-3 py-2 text-xs font-bold ${unreadOnly ? "border-[#8F740D] bg-[#F7F0DA] text-[#6A5B00]" : "border-[#CEC6B0]/60"}`}
          >
            Unread only
          </button>
          <button
            type="button"
            disabled={readAll.isPending}
            onClick={() => readAll.mutate()}
            className="inline-flex items-center gap-2 rounded-xl bg-[#1A1C1C] px-3 py-2 text-xs font-bold text-white disabled:opacity-60"
          >
            <CheckCheck className="h-4 w-4" /> Mark all read
          </button>
        </div>
      )}

      <section className="overflow-hidden rounded-2xl border border-[#CEC6B0]/50 bg-white">
        {view === "personal" && (
          personal.isLoading ? (
            <LoadingState />
          ) : personal.isError ? (
            <ErrorState message="Personal account activity could not be loaded." />
          ) : personal.data?.items.length ? (
            <div className="divide-y divide-[#F4F1E8]">
              {personal.data.items.map((item) => (
                <article key={item.uuid} className="flex gap-4 p-5">
                  <IconBox icon={<ShieldCheck className="h-4 w-4" />} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-[#8F740D]">{label(item.activity_type)}</p>
                      <time className="shrink-0 text-xs text-[#756F60]">{formatDate(item.created_at)}</time>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-[#625D4F]">{item.description}</p>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState title="No personal activity" body="Login, password, security, and other personal account events will appear here." />
          )
        )}

        {view === "organization" && (
          organization.isLoading ? (
            <LoadingState />
          ) : organization.isError ? (
            <ErrorState message="Organization activity could not be loaded." />
          ) : organization.data?.items.length ? (
            <div className="divide-y divide-[#F4F1E8]">
              {organization.data.items.map((item) => (
                <article key={item.uuid} className="flex gap-4 p-5">
                  <IconBox icon={<Building2 className="h-4 w-4" />} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-wider text-[#8F740D]">{label(item.activity_type)}</p>
                        <h2 className="mt-1 text-sm font-bold">{item.title}</h2>
                      </div>
                      <time className="shrink-0 text-xs text-[#756F60]">{formatDate(item.created_at)}</time>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState title="No organization activity" body="Team, invitation, role, and organization events will appear here." />
          )
        )}

        {view === "system" && (
          system.isLoading ? (
            <LoadingState />
          ) : system.isError ? (
            <ErrorState message="System notifications could not be loaded." />
          ) : system.data?.items.length ? (
            <div className="divide-y divide-[#F4F1E8]">
              {system.data.items.map((item) => (
                <article key={item.uuid} className={`flex gap-4 p-5 ${item.read_at ? "bg-white" : "bg-[#FFFCF3]"}`}>
                  <IconBox icon={<Bell className="h-4 w-4" />} muted={Boolean(item.read_at)} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-wider text-[#8F740D]">{label(item.notification_type)}</p>
                        <h2 className="mt-1 text-sm font-bold">{item.title}</h2>
                      </div>
                      <time className="shrink-0 text-xs text-[#756F60]">{formatDate(item.created_at)}</time>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-[#625D4F]">{item.body}</p>
                    {!item.read_at && (
                      <button type="button" onClick={() => read.mutate(item.uuid)} className="mt-3 inline-flex items-center gap-1.5 text-xs font-bold text-[#6A5B00]">
                        <MailOpen className="h-3.5 w-3.5" /> Mark as read
                      </button>
                    )}
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState title="No system notifications" body="Campaign, engagement, billing, and system events will appear here." />
          )
        )}
      </section>
      </PageSection>
    </PageContainer>
  );
};

const LoadingState = () => (
  <div className="grid min-h-64 place-items-center"><Loader2 className="h-5 w-5 animate-spin text-[#8F740D]" /></div>
);

const ErrorState = ({ message }: { message: string }) => (
  <p className="m-5 rounded-xl bg-red-50 p-4 text-sm text-red-800">{message}</p>
);

const EmptyState = ({ title, body }: { title: string; body: string }) => (
  <div className="grid min-h-64 place-items-center p-8 text-center">
    <div><Bell className="mx-auto h-8 w-8 text-[#C4BDAA]" /><h2 className="mt-3 font-bold">{title}</h2><p className="mt-1 text-sm text-[#756F60]">{body}</p></div>
  </div>
);

const IconBox = ({ icon, muted = false }: { icon: React.ReactNode; muted?: boolean }) => (
  <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${muted ? "bg-[#F4F1E8] text-[#756F60]" : "bg-[#F1D442]/20 text-[#8F740D]"}`}>
    {icon}
  </div>
);
