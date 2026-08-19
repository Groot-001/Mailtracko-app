import { z } from "zod";

const companyDomainPattern = /^(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i;

const optionalUrl = (label: string, maxLength: number) =>
  z
    .string()
    .trim()
    .max(maxLength, `${label} cannot exceed ${maxLength} characters.`)
    .refine((value) => {
      if (!value) return true;
      try {
        const url = new URL(value);
        return (url.protocol === "http:" || url.protocol === "https:") && Boolean(url.hostname);
      } catch {
        return false;
      }
    }, `${label} must be a valid URL starting with http:// or https://.`);

export const organizationSettingsSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Organization name must contain at least 2 characters.")
    .max(50, "Organization name cannot exceed 50 characters."),
  website_url: optionalUrl("Website URL", 200),
  domain_email: z
    .string()
    .trim()
    .toLowerCase()
    .max(253, "Company email domain cannot exceed 253 characters.")
    .refine((value) => !value || companyDomainPattern.test(value), "Enter a company email domain such as example.com."),
  timezone: z.string().trim().min(1, "Timezone is required.").max(255, "Timezone is too long."),
  org_logo: optionalUrl("Logo URL", 500),
});

export type OrganizationSettingsValues = z.infer<typeof organizationSettingsSchema>;
