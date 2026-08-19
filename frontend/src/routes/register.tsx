import { createFileRoute } from '@tanstack/react-router'
import { z } from "zod";
import CreateAccount from "../feature/login/components/Register";

const registerSearchSchema = z.object({
  token: z.string().optional(),
});

export const Route = createFileRoute("/register")({
  validateSearch: registerSearchSchema,
  component: CreateAccount,
});
