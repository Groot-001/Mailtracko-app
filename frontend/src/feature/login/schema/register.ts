import { z } from "zod";

export const createAccountSchema = z.object({
  full_name: z.string().min(1, "Full name is required"),
  email: z.string().email("Enter a valid email address"),
  password: z
    .string()
    .min(12, "Must be at least 12 characters including a symbol")
    .regex(/[^A-Za-z0-9]/, "Must be at least 12 characters including a symbol"),
  invite_token: z.string().optional(),
});

export type createAccountFormData = z.infer<typeof createAccountSchema>;
