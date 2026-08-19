import { createFileRoute } from "@tanstack/react-router";
import { BillingPlan } from "../../../../feature/organization/components/account-settings/BillingPlan";

export const Route = createFileRoute("/_protected/organization/account-settings/billing")({
  component: BillingPlan,
});
