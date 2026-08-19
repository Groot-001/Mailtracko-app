import { createFileRoute } from "@tanstack/react-router";
import { AccountSettingsLayout } from "../../../../feature/organization/components/account-settings/AccountSettingsLayout";

export const Route = createFileRoute("/_protected/organization/account-settings")({
  component: AccountSettingsLayout,
});
