import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState = ({ icon: Icon, title, description, action }: EmptyStateProps) => (
  <div className="flex flex-col items-center justify-center py-14 px-6 text-center gap-3">
    <div className="w-12 h-12 rounded-xl bg-[#F4F3F3] flex items-center justify-center">
      <Icon className="w-6 h-6 text-[#4C4736]" />
    </div>
    <div>
      <p className="text-sm font-semibold text-[#1A1C1C]">{title}</p>
      {description && (
        <p className="text-xs text-[#4C4736] mt-1 max-w-xs mx-auto">{description}</p>
      )}
    </div>
    {action && <div className="mt-2">{action}</div>}
  </div>
);
