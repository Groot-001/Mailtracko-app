import { createFileRoute } from "@tanstack/react-router";
import { GoogleSheetsSync } from "../../../feature/contacts/components/GoogleSheetsSync";

export const Route = createFileRoute("/_protected/contacts/google-sheets")({
  component: GoogleSheetsSync,
});
