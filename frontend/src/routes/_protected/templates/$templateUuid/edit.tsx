import { createFileRoute } from "@tanstack/react-router";
import { TemplateWizard } from "../../../../feature/templates/components/TemplateWizard";

export const Route = createFileRoute("/_protected/templates/$templateUuid/edit")({
  component: TemplateEditRoute,
});

function TemplateEditRoute() {
  const { templateUuid } = Route.useParams();
  return <TemplateWizard templateUuid={templateUuid} />;
}
