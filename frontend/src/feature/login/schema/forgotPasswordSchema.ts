import { z } from "zod";

export const forgotPasswordSchema = z.object({
  email: z
    .string()
    .trim()
    .min(1, "Email is required")
    .max(254, "Email cannot exceed 254 characters")
    .email("Enter a valid email address"),
});

export type forgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;
