import { z } from "zod";

export const verifyEmailSchema = z.object({
  token: z
    .string()
    .length(6, "Code must be 6 digits")
    .regex(/^\d+$/, "Code must be numeric"),
});

export type VerifyEmailFormData = z.infer<typeof verifyEmailSchema>;
