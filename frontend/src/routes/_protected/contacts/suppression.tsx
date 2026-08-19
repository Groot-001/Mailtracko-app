import { createFileRoute } from "@tanstack/react-router";
import { SuppressionList } from "../../../feature/contacts/components/SuppressionList";

export const Route = createFileRoute("/_protected/contacts/suppression")({
  component: SuppressionList,
});
