import { createFileRoute } from "@tanstack/react-router";
import { TemplateWizard } from "../../../feature/templates/components/TemplateWizard";

export const Route = createFileRoute("/_protected/templates/new")({
  component: TemplateWizard,
});
