import type { ReactNode } from "react";

interface PageSectionProps {
  children: ReactNode;
  className?: string;
}

export function PageSection({ children, className = "" }: PageSectionProps) {
  return (
    <section className={`mt-6 ${className}`}>
      {children}
    </section>
  );
}
