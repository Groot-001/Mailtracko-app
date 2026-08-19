import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { Building2, LayoutDashboard, Settings, ShieldAlert, Users } from "lucide-react";

const organizationTabs = [
  { label: "Overview", to: "/organization", icon: LayoutDashboard },
  { label: "Team", to: "/organization/team", icon: Users },
  { label: "Organization Settings", to: "/organization/settings", icon: Settings },
  { label: "Security", to: "/organization/security", icon: ShieldAlert },
] as const;

const isTabActive = (pathname: string, to: string) => {
  if (to === "/organization") {
    return pathname === "/organization" || pathname === "/organization/";
  }
  return pathname === to || pathname.startsWith(`${to}/`);
};

/**
 * Organization routes already live inside the global ProductShell. This layout
 * intentionally provides only organization-local navigation, avoiding the
 * duplicate sidebars/header states that previously made Account Settings and
 * Sender Accounts look selected at the same time.
 */
export const OrganizationLayout = () => {
  const pathname = useRouterState({ select: (state) => state.location.pathname });

  const isAccountSettings = pathname.startsWith("/organization/account-settings");
  if (isAccountSettings) {
    return <Outlet />;
  }

  const isNotifications = pathname.startsWith("/organization/notifications");

  return (
    <div className="mx-auto w-full max-w-[1480px] px-4 py-6 sm:px-6 lg:px-8">
      <section className="overflow-hidden rounded-2xl border border-[#E8DFC5] bg-white shadow-sm">
        <header className="border-b border-[#EEE9DB] bg-[#FFFCF3] px-5 py-5 sm:px-6">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F4EACB] text-[#8F740D]">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-[#111827]">
                {isNotifications ? "Notification Center" : "Organization"}
              </h1>
              <p className="mt-1 text-sm text-[#776E56]">
                {isNotifications
                  ? "Review workspace alerts and organization activity from one place."
                  : "Manage your workspace profile, team access, security, and settings."}
              </p>
            </div>
          </div>

          {!isNotifications && (
            <nav className="mt-5 flex gap-1 overflow-x-auto pb-1" aria-label="Organization sections">
              {organizationTabs.map(({ label, to, icon: Icon }) => {
                const active = isTabActive(pathname, to);
                return (
                  <Link
                    key={to}
                    to={to}
                    className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
                      active
                        ? "bg-[#F1D442]/20 text-[#7A6208]"
                        : "text-[#5E6471] hover:bg-white hover:text-[#111827]"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </Link>
                );
              })}
            </nav>
          )}
        </header>

        <div className="min-w-0 bg-[#FAFAF8] p-4 sm:p-6">
          <Outlet />
        </div>
      </section>
    </div>
  );
};
