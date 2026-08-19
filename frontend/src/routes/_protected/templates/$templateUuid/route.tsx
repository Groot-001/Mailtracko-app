import { Outlet, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_protected/templates/$templateUuid")({
  component: TemplateResourceLayout,
});

function TemplateResourceLayout() {
  return <Outlet />;
}
