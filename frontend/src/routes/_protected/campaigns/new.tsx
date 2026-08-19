import { createFileRoute } from "@tanstack/react-router";
import { CampaignWizard } from "../../../feature/campaigns/components/CampaignWizard";

export const Route = createFileRoute("/_protected/campaigns/new")({
  component: CampaignWizard,
});
