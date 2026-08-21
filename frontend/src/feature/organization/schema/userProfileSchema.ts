import { z } from "zod";

export const userProfileSchema = z.object({
  full_name: z
    .string()
    .trim()
    .min(2, "Full name must contain at least 2 characters.")
    .max(50, "Full name cannot exceed 50 characters."),
  phone: z
    .string()
    .trim()
    .max(20, "Phone number cannot exceed 20 characters.")
    .regex(/^[0-9\s\-()]*$/, "Phone number contains invalid characters.")
    .optional()
    .or(z.literal("")),
  country_code: z
    .string()
    .trim()
    .min(1, "Country code is required.")
    .max(10, "Country code is too long."),
  timezone: z
    .string()
    .trim()
    .min(1, "Timezone is required.")
    .max(100, "Timezone is too long."),
  location: z
    .string()
    .trim()
    .max(100, "Location cannot exceed 100 characters.")
    .optional()
    .or(z.literal("")),
  profile_image: z
    .string()
    .optional()
    .or(z.literal("")),
});

export type UserProfileValues = z.infer<typeof userProfileSchema>;
