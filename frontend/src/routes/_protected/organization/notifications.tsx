// This route matches the plural path used by application navigation.
import { createFileRoute } from "@tanstack/react-router";
import { NotificationsPage } from "../../../feature/organization/components/notifications/NotificationsPage";

export const Route = createFileRoute("/_protected/organization/notifications")({
  component: NotificationsPage,
});
