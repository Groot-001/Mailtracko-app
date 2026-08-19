import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Bell,
  Building2,
  ChevronDown,
  FileText,
  LayoutDashboard,
  Users,
  Send,
  Mail,
  Menu,
  Megaphone,
  Settings,
  LogOut,
  LifeBuoy,
  Shield,
  X,
  Sun,
  Moon,
  Loader2,
} from "lucide-react";
import { logoutAccount, updateProfile } from "../api/authApi";
import { clearPendingInvitationToken } from "../auth/pendingInvitation";
import { queryClient } from "../api/queryClient";
import { useAuthStore } from "../store/AuthStore";
import { getPlatformAccess } from "../../feature/platform/api/platformApi";

interface ProductShellProps {
  children: ReactNode;
}

const navigationItems = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Contacts", to: "/contacts", icon: Users },
  { label: "Templates", to: "/templates", icon: FileText },
  { label: "Campaigns", to: "/campaigns", icon: Megaphone },
  { label: "Sender Accounts", to: "/organization/account-settings/email-accounts", icon: Send },
  { label: "Organization", to: "/organization", icon: Building2 },
  { label: "Support", to: "/support", icon: LifeBuoy },
] as const;

const initialsFromName = (name?: string, email?: string) => {
  const source = name?.trim() || email?.trim() || "User";
  const parts = source.split(/\s+/).filter(Boolean);
  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
};

interface SidebarProps {
  pathname: string;
  close?: () => void;
  requestLogout: () => void;
  isPlatformAdmin?: boolean;
  hasWorkspace?: boolean;
}

const Sidebar = ({
  pathname,
  close,
  requestLogout,
  isPlatformAdmin,
  hasWorkspace = true,
}: SidebarProps) => {
  const user = useAuthStore((state) => state.user);

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex items-center gap-3 border-b border-[#EEE9DB] px-6 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#8F740D] shadow-sm">
          <Mail className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-base font-bold tracking-tight text-[#111827]">MailTracko</p>
          <p className="text-[11px] text-[#8A8067]">Email outreach workspace</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
        {hasWorkspace && navigationItems.map(({ label, to, icon: Icon }) => {
          const senderAccountsPath = "/organization/account-settings/email-accounts";
          const isSenderAccountsPath =
            pathname === senderAccountsPath ||
            pathname.startsWith(`${senderAccountsPath}/`);

          const active = isSenderAccountsPath
            ? to === senderAccountsPath
            : pathname === to || pathname.startsWith(`${to}/`);
          return (
            <Link
              key={label}
              to={to}
              onClick={close}
              className={`flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-medium transition-colors ${
                active
                  ? "bg-[#F7F0DA] text-[#7A6208]"
                  : "text-[#4C5365] hover:bg-[#F8F7F2] hover:text-[#111827]"
              }`}
            >
              <Icon className={`h-[18px] w-[18px] ${active ? "text-[#8F740D]" : ""}`} />
              {label}
            </Link>
          );
        })}
        {isPlatformAdmin && (
          <Link
            to="/admin"
            onClick={close}
            className={`flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-medium transition-colors ${
              pathname.startsWith("/admin")
                ? "bg-[#F7F0DA] text-[#7A6208]"
                : "text-[#4C5365] hover:bg-[#F8F7F2] hover:text-[#111827]"
            }`}
          >
            <Shield className="h-[18px] w-[18px]" /> Platform Admin
          </Link>
        )}
      </nav>

      {hasWorkspace ? (
        <div className="m-4 rounded-2xl border border-[#E8DFC5] bg-[#FFFCF3] p-4">
          <p className="text-xs font-semibold text-[#403919]">Campaign workspace</p>
          <p className="mt-1 text-[11px] leading-4 text-[#776E56]">
            Build regular, sequence, and A/B campaigns from one connected workflow.
          </p>
        </div>
      ) : (
        <div className="m-4 rounded-2xl border border-[#E8DFC5] bg-[#FFFCF3] p-4">
          <p className="text-xs font-semibold text-[#403919]">Platform administration</p>
          <p className="mt-1 text-[11px] leading-4 text-[#776E56]">
            This operator account is not attached to a customer workspace.
          </p>
        </div>
      )}

      <div className="border-t border-[#EEE9DB] p-4">
        <div className="flex items-center gap-3 rounded-xl p-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#F4EACB] text-xs font-bold text-[#7A6208]">
            {initialsFromName(user?.full_name, user?.email)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-semibold text-[#111827]">
              {user?.full_name || "MailTracko User"}
            </p>
            <p className="truncate text-[10px] text-[#8A8067]">{user?.email}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            close?.();
            requestLogout();
          }}
          className="mt-1 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-[#A43B35] transition-colors hover:bg-[#FFF1EF]"
        >
          <LogOut className="h-[18px] w-[18px]" />
          Log out
        </button>
      </div>
    </div>
  );
};

interface LogoutDialogProps {
  open: boolean;
  isPending: boolean;
  errorMessage: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

const LogoutDialog = ({
  open,
  isPending,
  errorMessage,
  onCancel,
  onConfirm,
}: LogoutDialogProps) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center px-4">
      <button
        type="button"
        aria-label="Cancel logout"
        onClick={onCancel}
        disabled={isPending}
        className="absolute inset-0 bg-black/40 backdrop-blur-[1px]"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="logout-title"
        className="relative w-full max-w-md rounded-2xl border border-[#E8DFC5] bg-white p-6 shadow-2xl"
      >
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#FFF1EF] text-[#A43B35]">
          <LogOut className="h-5 w-5" />
        </div>
        <h2 id="logout-title" className="mt-4 text-lg font-bold text-[#111827]">
          Log out of MailTracko?
        </h2>
        <p className="mt-2 text-sm leading-6 text-[#68604E]">
          Your current session will be revoked. You will need to sign in again to access your workspace.
        </p>
        {errorMessage && (
          <p role="alert" className="mt-3 rounded-xl bg-[#FFF1EF] px-3 py-2 text-sm text-[#A43B35]">
            {errorMessage}
          </p>
        )}
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={isPending}
            className="rounded-xl border border-[#DED7C5] px-4 py-2.5 text-sm font-semibold text-[#514A38] hover:bg-[#F8F7F2] disabled:cursor-not-allowed disabled:opacity-60"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isPending}
            className="inline-flex min-w-24 items-center justify-center gap-2 rounded-xl bg-[#A43B35] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#8F302B] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isPending ? "Logging out..." : "Log out"}
          </button>
        </div>
      </div>
    </div>
  );
};

export const ProductShell = ({ children }: ProductShellProps) => {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const clearAuth = useAuthStore((state) => state.logout);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);
  const [themeOverride, setThemeOverride] = useState<"light" | "dark" | null>(null);
  const selectedTheme = themeOverride ?? (user?.theme === "dark" ? "dark" : "light");
  const [themeSaving, setThemeSaving] = useState(false);
  const [themeError, setThemeError] = useState<string | null>(null);
  const platformAccess = useQuery({
    queryKey: ["platform", "access"],
    queryFn: getPlatformAccess,
    staleTime: 5 * 60 * 1000,
  });
  const accountMenuRef = useRef<HTMLDivElement>(null);
  const mobileCloseRef = useRef<HTMLButtonElement | null>(null);

  const logoutMutation = useMutation({
    mutationFn: logoutAccount,
    onSuccess: async () => {
      queryClient.clear();
      clearAuth();
      clearPendingInvitationToken();
      setLogoutDialogOpen(false);
      setAccountMenuOpen(false);
      await navigate({ to: "/login", replace: true });
    },
  });

  useEffect(() => {
    if (!accountMenuOpen) return;

    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!accountMenuRef.current?.contains(event.target as Node)) {
        setAccountMenuOpen(false);
      }
    };

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setAccountMenuOpen(false);
    };

    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [accountMenuOpen]);

  useEffect(() => {
    if (mobileOpen) {
      // focus the close button for keyboard users when mobile nav opens
      setTimeout(() => mobileCloseRef.current?.focus(), 0);
    }
  }, [mobileOpen]);

  useEffect(() => {
    document.documentElement.dataset.theme = selectedTheme;
  }, [selectedTheme]);


  const handleThemeToggle = async () => {
    const nextTheme = selectedTheme === "dark" ? "light" : "dark";

    setThemeError(null);
    setThemeOverride(nextTheme);
    setThemeSaving(true);

    try {
      const updatedUser = await updateProfile({ theme: nextTheme });
      setUser(updatedUser);
      setThemeOverride(null);
    } catch {
      setThemeOverride(null);
      setThemeError("Could not save theme. Please try again.");
    } finally {
      setThemeSaving(false);
    }
  };

  const requestLogout = () => {
    logoutMutation.reset();
    setAccountMenuOpen(false);
    setLogoutDialogOpen(true);
  };

  const logoutError = logoutMutation.isError
    ? "We could not revoke your session. Check your connection and try again."
    : null;

  return (
    <div className="min-h-screen bg-[#FBFAF6] text-[#111827]">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[232px] border-r border-[#EEE9DB] bg-white lg:block">
        <Sidebar
          pathname={pathname}
          requestLogout={requestLogout}
          isPlatformAdmin={platformAccess.data?.is_platform_admin}
          hasWorkspace={Boolean(platformAccess.data?.organization_uuid)}
        />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
            className="absolute inset-0 bg-black/30"
          />
          <aside className="relative h-full w-[285px] shadow-2xl">
            <button
              type="button"
              onClick={() => setMobileOpen(false)}
              ref={mobileCloseRef}
              className="absolute right-3 top-4 z-10 rounded-lg p-2 text-[#655D48] hover:bg-[#F5F1E6] focus-visible:outline focus-visible:outline-3 focus-visible:outline-offset-2"
              aria-label="Close menu"
            >
              <X className="h-5 w-5" />
            </button>
            <Sidebar
              pathname={pathname}
              close={() => setMobileOpen(false)}
              requestLogout={requestLogout}
              isPlatformAdmin={platformAccess.data?.is_platform_admin}
              hasWorkspace={Boolean(platformAccess.data?.organization_uuid)}
            />
          </aside>
        </div>
      )}

      <div className="lg:pl-[232px]">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-[#EEE9DB] bg-white/95 px-4 backdrop-blur sm:px-7">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="rounded-lg p-2 text-[#514A38] hover:bg-[#F6F2E7] lg:hidden"
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="hidden text-xs text-[#8A8067] lg:block">MailTracko Workspace</div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => void navigate({ to: "/organization/notifications" })}
              className="relative rounded-full p-2 text-[#4C5365] hover:bg-[#F7F4EA]"
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[#8F740D] ring-2 ring-white" />
            </button>
            <button
              type="button"
              onClick={() => void handleThemeToggle()}
              disabled={themeSaving}
              aria-label={selectedTheme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
              className="rounded-full p-2 text-[#4C5365] hover:bg-[#F7F4EA] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {themeSaving ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : selectedTheme === "dark" ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </button>
            {themeError ? (
              <p role="status" aria-live="polite" className="text-[11px] text-[#A43B35]">
                {themeError}
              </p>
            ) : null}
            <div className="h-6 w-px bg-[#E9E3D4]" />
            <div ref={accountMenuRef} className="relative">
              <button
                type="button"
                onClick={() => setAccountMenuOpen((open) => !open)}
                aria-expanded={accountMenuOpen}
                aria-haspopup="menu"
                className="flex items-center gap-2 rounded-xl p-1.5 hover:bg-[#F7F4EA]"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#F4EACB] text-xs font-bold text-[#7A6208]">
                  {initialsFromName(user?.full_name, user?.email)}
                </div>
                <ChevronDown
                  className={`h-4 w-4 text-[#8A8067] transition-transform ${accountMenuOpen ? "rotate-180" : ""}`}
                />
              </button>

              {accountMenuOpen && (
                <div
                  role="menu"
                  className="absolute right-0 mt-2 w-64 overflow-hidden rounded-2xl border border-[#E8DFC5] bg-white p-2 shadow-xl"
                >
                  <div className="border-b border-[#EEE9DB] px-3 py-2.5">
                    <p className="truncate text-sm font-semibold text-[#111827]">
                      {user?.full_name || "MailTracko User"}
                    </p>
                    <p className="truncate text-xs text-[#8A8067]">{user?.email}</p>
                  </div>
                  <Link
                    to="/organization/account-settings"
                    role="menuitem"
                    onClick={() => setAccountMenuOpen(false)}
                    className="mt-1 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-[#4C5365] hover:bg-[#F8F7F2] hover:text-[#111827]"
                  >
                    <Settings className="h-4 w-4" />
                    Account settings
                  </Link>
                  <button
                    type="button"
                    role="menuitem"
                    onClick={requestLogout}
                    className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-[#A43B35] hover:bg-[#FFF1EF]"
                  >
                    <LogOut className="h-4 w-4" />
                    Log out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="min-h-[calc(100vh-4rem)]">{children}</main>
      </div>

      <LogoutDialog
        open={logoutDialogOpen}
        isPending={logoutMutation.isPending}
        errorMessage={logoutError}
        onCancel={() => {
          if (!logoutMutation.isPending) {
            logoutMutation.reset();
            setLogoutDialogOpen(false);
          }
        }}
        onConfirm={() => logoutMutation.mutate()}
      />
    </div>
  );
};
