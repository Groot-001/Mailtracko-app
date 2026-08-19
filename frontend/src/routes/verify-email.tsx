// src/routes/verify-email.tsx
import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import VerifyEmail from "../feature/login/components/VerifyEmail";

const verifyEmailSearchSchema = z.object({
  email: z.string().email(),
  // The session lives in an HttpOnly cookie, so no credential is exposed in
  // the URL.
});

export const Route = createFileRoute("/verify-email")({
  validateSearch: verifyEmailSearchSchema,
  component: VerifyEmail,
});
