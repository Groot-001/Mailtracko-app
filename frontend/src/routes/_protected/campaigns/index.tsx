import { createFileRoute } from "@tanstack/react-router";
import { CampaignDashboard } from "../../../feature/campaigns/components/CampaignDashboard";

export const Route = createFileRoute("/_protected/campaigns/")({
  component: CampaignDashboard,
});
