import { createFileRoute } from "@tanstack/react-router";
import { CampaignWizard } from "../../../../feature/campaigns/components/CampaignWizard";

export const Route = createFileRoute("/_protected/campaigns/$campaignUuid/edit")({
  component: CampaignEditRoute,
});

function CampaignEditRoute() {
  const { campaignUuid } = Route.useParams();
  return <CampaignWizard campaignUuid={campaignUuid} />;
}
