// src/routes/_protected/organization/security.tsx
import { createFileRoute } from "@tanstack/react-router";
import { AccountActions } from "../../../feature/organization/components/security/AccountActions";

export const Route = createFileRoute("/_protected/organization/security")({
  component: AccountActions,
});
