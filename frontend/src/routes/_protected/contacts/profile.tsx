import { createFileRoute } from "@tanstack/react-router";
import { ContactProfile } from "../../../feature/contacts/components/ContactProfile";
import { z } from "zod/v4";

const searchSchema = z.object({
  listUuid: z.string(),
  contactUuid: z.string(),
});

export const Route = createFileRoute("/_protected/contacts/profile")({
  validateSearch: (search) => searchSchema.parse(search),
  component: ContactProfile,
});
