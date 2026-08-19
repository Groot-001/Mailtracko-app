import { createFileRoute } from "@tanstack/react-router";
import { AccountNotifications } from "../../../../feature/organization/components/account-settings/AccountNotifications";

export const Route = createFileRoute("/_protected/organization/account-settings/notifications")({
  component: AccountNotifications,
});
