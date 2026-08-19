import { createFileRoute } from "@tanstack/react-router";
import { ContactsDashboard } from "../../../feature/contacts/components/ContactsDashboard";
import { z } from "zod/v4";

const contactsSearchSchema = z.object({
  listUuid: z.string().optional(),
});

export const Route = createFileRoute("/_protected/contacts/")({
  validateSearch: (search) => contactsSearchSchema.parse(search),
  component: ContactsDashboard,
});
