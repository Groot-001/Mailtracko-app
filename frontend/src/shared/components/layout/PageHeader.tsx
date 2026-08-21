import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  description?: string | ReactNode;
  actions?: ReactNode;
  breadcrumbs?: ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  actions,
  breadcrumbs,
  className = "",
}: PageHeaderProps) {
  return (
    <div className={`flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between ${className}`}>
      <div className="min-w-0 flex-1">
        {breadcrumbs && <div className="mb-1 text-xs text-[#756E5C] dark:text-slate-400">{breadcrumbs}</div>}
        <h1 className="text-3xl font-bold tracking-tight text-[#111827] dark:text-white">
          {title}
        </h1>
        {description && (
          <p className="mt-1.5 text-sm text-[#756E5C] dark:text-slate-400">
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex flex-wrap items-center gap-2 shrink-0 sm:mt-0">
          {actions}
        </div>
      )}
    </div>
  );
}
