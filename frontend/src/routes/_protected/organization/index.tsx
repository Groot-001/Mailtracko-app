import { createFileRoute } from "@tanstack/react-router";
import { OrganizationOverview } from "../../../feature/organization/components/overview/OrganizationOverview";

export const Route = createFileRoute("/_protected/organization/")({
  component: OrganizationOverview,
});
