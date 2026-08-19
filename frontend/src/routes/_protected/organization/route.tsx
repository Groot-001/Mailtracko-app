import { createFileRoute } from "@tanstack/react-router";
import { OrganizationLayout } from "../../../feature/organization/components/layout/OrganizationLayout";

export const Route = createFileRoute("/_protected/organization")({
  component: OrganizationLayout,
});
