import { Outlet, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_protected/campaigns/$campaignUuid")({
  component: CampaignResourceLayout,
});

function CampaignResourceLayout() {
  return <Outlet />;
}
