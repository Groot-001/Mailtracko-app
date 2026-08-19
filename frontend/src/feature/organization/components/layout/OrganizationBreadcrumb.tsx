import { Link, useMatchRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import type { LinkProps } from "@tanstack/react-router";

interface BreadcrumbSegment {
  label: string;
  to?: LinkProps["to"];
}

interface OrganizationBreadcrumbProps {
  segments: BreadcrumbSegment[];
}

export const OrganizationBreadcrumb = ({
  segments,
}: OrganizationBreadcrumbProps) => {
  return (
    <nav
      aria-label="Breadcrumb"
      className="flex items-center gap-1 text-sm text-[#4C4736]"
    >
      {segments.map((seg, idx) => {
        const isLast = idx === segments.length - 1;
        return (
          <span key={idx} className="flex items-center gap-1">
            {idx > 0 && <ChevronRight className="w-3.5 h-3.5 text-[#CEC6B0]" />}
            {!isLast && seg.to ? (
              <Link
                to={seg.to}
                className="hover:text-[#8F740D] transition-colors"
              >
                {seg.label}
              </Link>
            ) : (
              <span
                className={isLast ? "text-[#8F740D] font-medium" : ""}
                aria-current={isLast ? "page" : undefined}
              >
                {seg.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
};

// ─── Convenience hook for building org breadcrumbs ────────────────────────────

// OrganizationBreadcrumb.tsx — useOrganizationBreadcrumbs only, component unchanged
export const useOrganizationBreadcrumbs = (): BreadcrumbSegment[] => {
  const matchRoute = useMatchRoute();

  const isTeam = matchRoute({ to: "/organization/team" });
  const isRoles = matchRoute({ to: "/organization/team/roles" });
  const isNotifications = matchRoute({ to: "/organization/notifications" });
  const isSettings = matchRoute({ to: "/organization/settings" });
  const isSecurity = matchRoute({ to: "/organization/security" });
  const isOverview = matchRoute({ to: "/organization" });

  // Team and Roles share a breadcrumb — they're differentiated by an
  // in-page tab (TeamTabs), not by breadcrumb depth. Matches reference design.
  if (isTeam || isRoles) {
    return [{ label: "Organization", to: "/organization" }, { label: "Team" }];
  }
  if (isNotifications) {
    return [
      { label: "Organization", to: "/organization" },
      { label: "Notifications" },
    ];
  }
  if (isSettings) {
    return [
      { label: "Organization", to: "/organization" },
      { label: "Settings" },
    ];
  }
  if (isSecurity) {
    return [
      { label: "Organization", to: "/organization" },
      { label: "Security" },
    ];
  }
  if (isOverview) {
    return [{ label: "Organization" }];
  }

  return [];
};
