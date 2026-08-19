import { createFileRoute } from "@tanstack/react-router";
import { Dashboard } from "../../feature/onboarding/components/Dashboard";

export const Route = createFileRoute("/_protected/dashboard")({
  component: Dashboard,
});
