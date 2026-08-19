// src/feature/organization/components/team/TeamTabs.tsx
import { Link, useMatchRoute } from "@tanstack/react-router";
import { Users, ShieldCheck } from "lucide-react";

const TEAM_TABS = [
  { label: "Team Members", to: "/organization/team", icon: Users },
  {
    label: "Roles & Permissions",
    to: "/organization/team/roles",
    icon: ShieldCheck,
  },
] as const;

export const TeamTabs = () => {
  const matchRoute = useMatchRoute();

  return (
    <div className="flex items-center gap-1 border-b border-[#EEEEEE]">
      {TEAM_TABS.map((tab) => {
        const isActive = !!matchRoute({ to: tab.to });
        return (
          <Link
            key={tab.to}
            to={tab.to}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-all ${
              isActive
                ? "border-[#8F740D] text-[#8F740D]"
                : "border-transparent text-[#4C4736] hover:text-[#1A1C1C] hover:border-[#CEC6B0]"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
};
