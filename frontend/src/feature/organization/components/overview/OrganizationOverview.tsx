import {
  Building2,
  Users,
  ShieldCheck,
  ChevronRight,
  Globe,
  Calendar,
  Hash,
  Tag,
  Pencil,
  Upload,
  BadgeCheck,
  Settings,
  UserPlus,
  Lock,
  BarChart2,
  UserCog,
  Shield,
  Mail,
  MailOpen,
  CheckCircle2,
} from "lucide-react";
import { Link } from "@tanstack/react-router";
import { PageContainer } from "../../../../shared/components/layout";
import { useQuery } from "@tanstack/react-query";
import { useOrganization } from "../../hooks/useOrganization";
import { useMembers } from "../../hooks/useMembers";
import { usePendingInvitations } from "../../hooks/useInvitations";
import { useOrganizationActivities } from "../../hooks/useOrganizationActivities";
import { AvatarInitials } from "../shared/AvatarInitials";
import { getBillingOverview } from "../../../platform/api/platformApi";

// ─── Helpers ──────────────────────────────────────────────────────────────────

const formatTimeAgo = (isoDate: string): string => {
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hour${hrs === 1 ? "" : "s"} ago`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
};

// ─── Sub-components ───────────────────────────────────────────────────────────

interface StatCardProps {
  icon: React.ElementType;
  label: string;
  value: React.ReactNode;
  subtext?: React.ReactNode;
  to?: string;
}

const StatCard = ({ icon: Icon, label, value, subtext, to }: StatCardProps) => {
  const inner = (
    <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-5 flex flex-col gap-3 hover:shadow-md transition-shadow duration-200 cursor-pointer group">
      <div className="flex items-start justify-between">
        <div className="w-10 h-10 rounded-xl bg-[#F4F3F3] flex items-center justify-center">
          <Icon className="w-5 h-5 text-[#8F740D]" />
        </div>
        {to && (
          <ChevronRight className="w-4 h-4 text-[#CEC6B0] group-hover:text-[#8F740D] transition-colors" />
        )}
      </div>
      <div>
        <p className="text-xs text-[#4C4736] font-medium mb-0.5">{label}</p>
        <p className="text-xl font-bold text-[#1A1C1C]">{value}</p>
        {subtext && <p className="text-xs text-[#4C4736] mt-0.5">{subtext}</p>}
      </div>
    </div>
  );

  return to ? <Link to={to}>{inner}</Link> : inner;
};

// ─── Activity Icon ─────────────────────────────────────────────────────────────

const activityIconMap: Record<string, React.ElementType> = {
  member_added: UserPlus,
  member_removed: Users,
  invitation_sent: Mail,
  invitation_accepted: CheckCircle2,
  invitation_declined: MailOpen,
  invitation_revoked: MailOpen,
  organization_created: Building2,
  organization_updated: Settings,
  organization_deletion_requested: BarChart2,
};

const activityIconBgMap: Record<string, string> = {
  member_added: "bg-emerald-50 text-emerald-600",
  member_removed: "bg-red-50 text-red-500",
  invitation_sent: "bg-blue-50 text-blue-600",
  invitation_accepted: "bg-emerald-50 text-emerald-600",
  invitation_declined: "bg-orange-50 text-orange-600",
  invitation_revoked: "bg-gray-100 text-gray-500",
  organization_created: "bg-[#F1D442]/20 text-[#8F740D]",
  organization_updated: "bg-purple-50 text-purple-600",
  organization_deletion_requested: "bg-red-50 text-red-500",
};

// ─── Quick Actions ─────────────────────────────────────────────────────────────

// quickActions — fixed Security & Authentication target
const quickActions = [
  {
    label: "Team Management",
    sub: "Add, remove, and manage team members",
    icon: Users,
    to: "/organization/team",
  },
  {
    label: "Roles & Permissions",
    sub: "Manage roles and access levels",
    icon: ShieldCheck,
    to: "/organization/team/roles",
  },
  {
    label: "Security & Authentication",
    sub: "Configure security and authentication",
    icon: Lock,
    to: "/organization/security",
  },
] as const;

// ─── Settings Categories ──────────────────────────────────────────────────────

const settingsCategories = [
  {
    label: "Organization Settings",
    sub: "General organization configuration",
    icon: Settings,
    to: "/organization/settings",
  },
  {
    label: "Profile Management",
    sub: "Manage organization profile and branding",
    icon: UserCog,
    to: "/organization/settings",
  },
  {
    label: "Team Management",
    sub: "Manage team members and departments",
    icon: Users,
    to: "/organization/team",
  },
  {
    label: "Roles",
    sub: "Define roles and access permissions",
    icon: Shield,
    to: "/organization/team/roles",
  },
  {
    label: "Security & Authentication",
    sub: "Configure security policies and MFA",
    icon: Lock,
    to: "/organization/security",
  },
  {
    label: "Account Actions",
    sub: "Danger zone and account actions",
    icon: BarChart2,
    to: "/organization/security",
  },
] as const;

// ─── Main Component ───────────────────────────────────────────────────────────

export const OrganizationOverview = () => {
  const { data: org, isLoading: orgLoading } = useOrganization();
  const { data: membersData } = useMembers();
  const { data: pendingInvites } = usePendingInvitations();
  const { data: activities } = useOrganizationActivities({ limit: 5 });
  const { data: billing } = useQuery({
    queryKey: ["billing", "overview"],
    queryFn: getBillingOverview,
  });

  const activeCount =
    membersData?.items.filter((m) => m.status === "active").length ?? 0;
  const pendingCount = pendingInvites?.items.length ?? 0;
  const totalMembers = membersData?.total ?? 0;

  if (orgLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[#8F740D] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <PageContainer nested>
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-[#1A1C1C] tracking-tight">
          Organization Overview
        </h1>
        <p className="text-sm text-[#4C4736] mt-1">
          Manage your organization settings, team, security, and notifications
          in one place.
        </p>
      </div>

      {/* Top stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Building2}
          label="Organization Profile"
          value={org?.name ?? "—"}
          subtext={
            <span className="flex items-center gap-1">
              <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold">
                <BadgeCheck className="w-3.5 h-3.5" /> Verified
              </span>
              <span className="text-[#4C4736]">· Active</span>
            </span>
          }
          to="/organization"
        />
        <StatCard
          icon={Users}
          label="Team Members"
          value={totalMembers}
          subtext={`${activeCount} Active · ${pendingCount} Pending`}
          to="/organization/team"
        />

        <StatCard
          icon={ShieldCheck}
          label="Security"
          value="Manage"
          subtext="Review MFA, sessions, and account protection"
          to="/organization/security"
        />
        <StatCard
          icon={Mail}
          label="Pending Invites"
          value={pendingCount}
          subtext={pendingCount === 1 ? "1 invitation awaiting response" : `${pendingCount} invitations awaiting response`}
          to="/organization/team"
        />
      </div>

      {/* Two-column row: Profile + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6">
        {/* Organization Profile card */}
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-5">
          <h2 className="text-base font-semibold text-[#1A1C1C]">
            Organization Profile
          </h2>
          <div className="flex flex-col sm:flex-row gap-6">
            {/* Logo placeholder */}
            <div className="w-28 h-28 rounded-xl bg-gradient-to-br from-[#F1D442]/40 to-[#E2C635]/20 border border-[#CEC6B0]/40 flex items-center justify-center flex-shrink-0">
              {org?.org_logo ? (
                <img
                  src={org.org_logo}
                  alt="org logo"
                  className="w-full h-full object-cover rounded-xl"
                />
              ) : (
                <div className="w-12 h-12 rounded-full border-4 border-[#8F740D]/30 flex items-center justify-center">
                  <span className="text-2xl font-black text-[#8F740D]">
                    {org?.name?.[0] ?? "O"}
                  </span>
                </div>
              )}
            </div>

            {/* Meta */}
            <div className="flex-1 space-y-3">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-lg font-bold text-[#1A1C1C]">
                  {org?.name ?? "—"}
                </h3>
                <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 text-xs font-semibold px-2 py-0.5 rounded-full border border-emerald-200">
                  <BadgeCheck className="w-3 h-3" /> Verified
                </span>
              </div>

              <div className="space-y-2 text-sm text-[#4C4736]">
                {[
                  {
                    icon: Globe,
                    label: "Timezone",
                    value: org?.timezone ?? "UTC",
                  },
                  {
                    icon: Calendar,
                    label: "Created",
                    value: org?.created_at
                      ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(org.created_at))
                      : "Unavailable",
                  },
                  {
                    icon: Hash,
                    label: "Organization ID",
                    value: org?.uuid ? `org_${org.uuid.slice(0, 12)}` : "—",
                  },
                  {
                    icon: Tag,
                    label: "Plan",
                    value: billing?.subscription
                      ? `${billing.subscription.plan.name} · ${billing.subscription.status}`
                      : "No active subscription",
                  },
                ].map((row) => (
                  <div key={row.label} className="flex items-center gap-2">
                    <row.icon className="w-3.5 h-3.5 text-[#CEC6B0] flex-shrink-0" />
                    <span className="font-medium text-[#1A1C1C] w-28 flex-shrink-0">
                      {row.label}
                    </span>
                    <span>{row.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-2 pt-2 border-t border-[#EEEEEE]">
            <Link to="/organization/settings" className="flex items-center gap-1.5 px-4 py-2 bg-[#8F740D] hover:bg-[#6A5B00] text-white text-xs font-semibold rounded-lg transition-colors">
              <Pencil className="w-3.5 h-3.5" /> Edit Profile
            </Link>
            <Link to="/organization/settings" className="flex items-center gap-1.5 px-4 py-2 bg-white border border-[#CEC6B0]/60 hover:bg-[#F4F3F3] text-[#1A1C1C] text-xs font-semibold rounded-lg transition-colors">
              <Upload className="w-3.5 h-3.5" /> Upload Logo
            </Link>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-3">
          <h2 className="text-base font-semibold text-[#1A1C1C]">
            Quick actions
          </h2>
          <div className="space-y-1">
            {quickActions.map((action) => (
              <Link
                key={action.label}
                to={action.to}
                className="flex items-center gap-3 px-3 py-3 rounded-xl hover:bg-[#F4F3F3] transition-colors group"
              >
                <div className="w-8 h-8 rounded-lg bg-[#F4F3F3] group-hover:bg-[#F1D442]/20 flex items-center justify-center flex-shrink-0 transition-colors">
                  <action.icon className="w-4 h-4 text-[#8F740D]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#1A1C1C]">
                    {action.label}
                  </p>
                  <p className="text-xs text-[#4C4736] truncate">
                    {action.sub}
                  </p>
                </div>
                <ChevronRight className="w-4 h-4 text-[#CEC6B0] group-hover:text-[#8F740D] transition-colors flex-shrink-0" />
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Two-column row: Activity + Settings Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6">
        {/* Recent Activity */}
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-[#1A1C1C]">
              Recent organization activity
            </h2>
            <Link to="/organization/account-settings/activity" className="text-xs font-medium text-[#8F740D] hover:underline">
              View all activity
            </Link>
          </div>

          {activities?.items.length === 0 || !activities ? (
            <p className="text-sm text-[#4C4736] text-center py-8">
              No recent activity.
            </p>
          ) : (
            <div className="space-y-1">
              {activities.items.map((activity) => {
                const Icon =
                  activityIconMap[activity.activity_type] ?? Settings;
                const iconBg =
                  activityIconBgMap[activity.activity_type] ??
                  "bg-gray-100 text-gray-500";
                return (
                  <div
                    key={activity.uuid}
                    className="flex items-center gap-3 py-3 border-b border-[#EEEEEE] last:border-0"
                  >
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${iconBg}`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-[#1A1C1C] font-medium truncate">
                        {activity.title}
                      </p>
                      <p className="text-xs text-[#4C4736]">
                        {formatTimeAgo(activity.created_at)}
                      </p>
                    </div>
                    <AvatarInitials
                      name={null}
                      email={activity.target_email}
                      size="sm"
                    />
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Settings Categories */}
        <div className="bg-white border border-[#CEC6B0]/40 rounded-2xl p-6 space-y-4">
          <h2 className="text-base font-semibold text-[#1A1C1C]">
            Settings categories
          </h2>
          {/* <div className="grid grid-cols-2 gap-3">
            {settingsCategories.map((cat) => (
              <div
                key={cat.label}
                className="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-[#F4F3F3] transition-colors cursor-pointer group text-center"
              >
                <div className="w-9 h-9 rounded-lg bg-[#F4F3F3] group-hover:bg-[#F1D442]/20 flex items-center justify-center transition-colors">
                  <cat.icon className="w-4.5 h-4.5 text-[#8F740D]" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-[#1A1C1C] leading-tight">
                    {cat.label}
                  </p>
                  <p className="text-[10px] text-[#4C4736] mt-0.5 leading-tight">
                    {cat.sub}
                  </p>
                </div>
              </div>
            ))}
          </div> */}
          <div className="grid grid-cols-2 gap-3">
            {settingsCategories.map((cat) => (
              <Link
                key={cat.label}
                to={cat.to}
                className="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-[#F4F3F3] transition-colors group text-center"
              >
                <div className="w-9 h-9 rounded-lg bg-[#F4F3F3] group-hover:bg-[#F1D442]/20 flex items-center justify-center transition-colors">
                  <cat.icon className="w-4.5 h-4.5 text-[#8F740D]" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-[#1A1C1C] leading-tight">
                    {cat.label}
                  </p>
                  <p className="text-[10px] text-[#4C4736] mt-0.5 leading-tight">
                    {cat.sub}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </PageContainer>
  );
};
