import { z } from "zod";

export const createAccountSchema = z.object({
  full_name: z
    .string()
    .trim()
    .min(1, "Full name is required")
    .max(50, "Full name cannot exceed 50 characters"),
  email: z
    .string()
    .trim()
    .min(1, "Email is required")
    .max(254, "Email cannot exceed 254 characters")
    .email("Enter a valid email address"),
  password: z
    .string()
    .min(12, "Password must be at least 12 characters")
    .max(128, "Password cannot exceed 128 characters")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[a-z]/, "Password must contain at least one lowercase letter")
    .regex(/\d/, "Password must contain at least one number")
    .regex(
      /[!@#$%^&*()_+\-=[\]{}|;':",./<>?`~]/,
      "Password must contain at least one special character",
    ),
  invite_token: z.string().optional(),
});

export type createAccountFormData = z.infer<typeof createAccountSchema>;
