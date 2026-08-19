import { createFileRoute } from "@tanstack/react-router";
import { ImportReport } from "../../../feature/contacts/components/ImportReport";

export const Route = createFileRoute("/_protected/contacts/import-report")({
  component: ImportReport,
});
