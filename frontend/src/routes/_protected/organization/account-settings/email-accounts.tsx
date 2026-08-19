import { createFileRoute } from "@tanstack/react-router";
import { EmailAccountsDashboard } from "../../../../feature/email-accounts/components/EmailAccountsDashboard";
import { z } from "zod/v4";

const emailAccountsSearchSchema = z.object({
  success: z.string().optional(),
  error: z.string().optional(),
});

export const Route = createFileRoute(
  "/_protected/organization/account-settings/email-accounts"
)({
  validateSearch: (search) => emailAccountsSearchSchema.parse(search),
  component: EmailAccountsDashboard,
});
