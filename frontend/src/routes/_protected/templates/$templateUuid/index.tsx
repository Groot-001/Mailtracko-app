import { createFileRoute } from "@tanstack/react-router";
import { TemplateDetails } from "../../../../feature/templates/components/TemplateDetails";

export const Route = createFileRoute("/_protected/templates/$templateUuid/")({
  component: TemplateDetailsRoute,
});

function TemplateDetailsRoute() {
  const { templateUuid } = Route.useParams();
  return <TemplateDetails templateUuid={templateUuid} />;
}
