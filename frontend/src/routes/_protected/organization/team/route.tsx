// src/routes/_protected/organization/team/route.tsx
import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/_protected/organization/team")({
  component: () => <Outlet />,
});
