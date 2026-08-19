import { Outlet, Link, useMatchRoute, useRouterState } from "@tanstack/react-router";
import {
  User,
  ShieldCheck,
  Bell,
  CreditCard,
  ScrollText,
  Code2,
  Palette,
} from "lucide-react";

// ─── Settings sub-navigation items ────────────────────────────────────────────

interface SettingsNavItem {
  to: string;
  label: string;
  icon: React.ElementType;
}

const SETTINGS_NAV: SettingsNavItem[] = [
  { to: "/organization/account-settings", label: "Profile", icon: User },
  { to: "/organization/account-settings/security", label: "Security", icon: ShieldCheck },
  { to: "/organization/account-settings/preferences", label: "Appearance", icon: Palette },
  { to: "/organization/account-settings/notifications", label: "Notification Preferences", icon: Bell },
  { to: "/organization/account-settings/billing", label: "Billing & Plan", icon: CreditCard },
  { to: "/organization/account-settings/activity", label: "Activity Log", icon: ScrollText },
  { to: "/organization/account-settings/api-integrations", label: "API & Integrations", icon: Code2 },
];

// ─── Component ────────────────────────────────────────────────────────────────

export const AccountSettingsLayout = () => {
  const matchRoute = useMatchRoute();
  const pathname = useRouterState({ select: (state) => state.location.pathname });

  // Sender Accounts is a primary product section even though its legacy URL
  // lives under /account-settings. Do not wrap it in the personal Account
  // Settings navigation, otherwise two unrelated navigation areas appear
  // selected at once.
  if (
    pathname === "/organization/account-settings/email-accounts" ||
    pathname.startsWith("/organization/account-settings/email-accounts/")
  ) {
    return <Outlet />;
  }

  const isActive = (to: string) => {
    // Exact match for the index route (Profile)
    if (to === "/organization/account-settings") {
      return (
        !!matchRoute({ to, fuzzy: false }) &&
        !SETTINGS_NAV.slice(1).some((item) =>
          matchRoute({ to: item.to, fuzzy: true })
        )
      );
    }
    return !!matchRoute({ to, fuzzy: true });
  };

  return (
    <div className="mx-auto max-w-[1480px] space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-[#1A1C1C] tracking-tight">
          Account Settings
        </h1>
        <p className="text-sm text-[#4C4736] mt-1">
          Manage your account profile and personal information.
        </p>
      </div>

      {/* Content grid: sidebar tabs + page content */}
      <div className="flex flex-col md:flex-row gap-6">
        {/* Sub-navigation sidebar */}
        <nav className="w-full md:w-[200px] lg:w-[220px] shrink-0">
          {/* Desktop: vertical list */}
          <div className="hidden md:flex flex-col gap-0.5">
            {SETTINGS_NAV.map((item) => {
              const active = isActive(item.to);
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    active
                      ? "bg-[#F1D442]/20 text-[#8F740D]"
                      : "text-[#4C4736] hover:text-[#1A1C1C] hover:bg-[#F4F3F3]"
                  }`}
                >
                  <item.icon
                    className={`w-4 h-4 flex-shrink-0 ${
                      active ? "text-[#8F740D]" : "text-[#4C4736]"
                    }`}
                  />
                  {item.label}
                </Link>
              );
            })}
          </div>

          {/* Mobile: horizontal scroll */}
          <div className="flex md:hidden gap-1 overflow-x-auto pb-2 -mx-2 px-2 scrollbar-none">
            {SETTINGS_NAV.map((item) => {
              const active = isActive(item.to);
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                    active
                      ? "bg-[#F1D442]/20 text-[#8F740D]"
                      : "text-[#4C4736] hover:text-[#1A1C1C] hover:bg-[#F4F3F3]"
                  }`}
                >
                  <item.icon className="w-3.5 h-3.5 flex-shrink-0" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Page content */}
        <div className="flex-1 min-w-0">
          <Outlet />
        </div>
      </div>
    </div>
  );
};
