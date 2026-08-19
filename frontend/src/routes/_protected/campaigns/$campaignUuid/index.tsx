import { createFileRoute } from "@tanstack/react-router";
import { CampaignDetails } from "../../../../feature/campaigns/components/CampaignDetails";

export const Route = createFileRoute("/_protected/campaigns/$campaignUuid/")({
  component: CampaignDetailsRoute,
});

function CampaignDetailsRoute() {
  const { campaignUuid } = Route.useParams();
  return <CampaignDetails campaignUuid={campaignUuid} />;
}
