// src/routes/_protected/organization/team/index.tsx
import { createFileRoute } from "@tanstack/react-router";
import { TeamManagement } from "../../../../feature/organization/components/team/TeamManagement";

export const Route = createFileRoute("/_protected/organization/team/")({
  component: TeamManagement,
});
