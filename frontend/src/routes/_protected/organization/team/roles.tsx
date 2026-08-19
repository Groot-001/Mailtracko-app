// src/routes/_protected/organization/team/roles.tsx
import { createFileRoute } from "@tanstack/react-router";
import { RolesPermissions } from "../../../../feature/organization/components/roles/RolesPermissions";

export const Route = createFileRoute("/_protected/organization/team/roles")({
  component: RolesPermissions,
});
