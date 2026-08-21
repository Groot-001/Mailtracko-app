import type { ReactNode } from "react";

interface PageContainerProps {
  children: ReactNode;
  /**
   * If true, suppresses page-level max-width and outer horizontal padding.
   * Prevents layout container duplication inside nested route layouts.
   */
  nested?: boolean;
  /**
   * Layout container max-width configuration.
   * - "default" uses MailTracko standard 1480px.
   * - "narrow" uses 1280px (max-w-7xl) for content-focused grids/settings.
   * - "full" allows edge-to-edge spans.
   */
  size?: "default" | "narrow" | "full";
  className?: string;
}

export function PageContainer({
  children,
  nested = false,
  size = "default",
  className = "",
}: PageContainerProps) {
  if (nested) {
    return <div className={`space-y-6 ${className}`}>{children}</div>;
  }

  const maxWidthClass =
    size === "narrow"
      ? "max-w-7xl"
      : size === "full"
        ? "max-w-full"
        : "max-w-[1480px]";

  return (
    <div className={`mx-auto ${maxWidthClass} px-4 py-6 sm:px-6 lg:px-8 space-y-6 ${className}`}>
      {children}
    </div>
  );
}
