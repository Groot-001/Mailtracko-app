// src/routes/_protected/organization/settings.tsx
import { createFileRoute } from "@tanstack/react-router";
import { OrganizationSettings } from "../../../feature/organization/components/settings/OrganizationSettings";

export const Route = createFileRoute("/_protected/organization/settings")({
  component: OrganizationSettings,
});
