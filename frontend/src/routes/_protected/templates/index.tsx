import { createFileRoute } from "@tanstack/react-router";
import { TemplateDashboard } from "../../../feature/templates/components/TemplateDashboard";

export const Route = createFileRoute("/_protected/templates/")({
  component: TemplateDashboard,
});
