import { z } from "zod";

export const ORGANIZATION_SIZE_OPTIONS = [
  "1-10 employees",
  "11-50 employees",
  "51-200 employees",
  "201-500 employees",
  "500-1000 employees",
  "1000+ employees",
] as const;

export const EMAIL_VOLUME_OPTIONS = [
  "< 5,000",
  "5,000 - 25,000",
  "25,000 - 100,000",
  "100,000 - 500,000",
  "500,000+",
] as const;

export const INDUSTRY_OPTIONS = [
  "technology",
  "finance",
  "healthcare",
  "education",
  "ecommerce",
  "real_estate",
  "consulting",
  "manufacturing",
  "others",
] as const;

export const SOURCE_OPTIONS = [
  "referral",
  "linkedin",
  "youtube",
  "marketplace",
  "newsletter",
  "events_webinar",
  "social_media",
  "others",
] as const;

const domainPattern = /^(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i;

const websiteSchema = z
  .string()
  .trim()
  .min(3, "Website URL is required")
  .max(200, "Website URL cannot exceed 200 characters")
  .transform((value) => (/^https?:\/\//i.test(value) ? value : `https://${value}`))
  .pipe(z.string().url("Enter a valid website URL"));

export const organizationStepSchema = z.object({
  organizationName: z
    .string()
    .trim()
    .min(2, "Organization name must be at least 2 characters")
    .max(50, "Organization name cannot exceed 50 characters"),
  websiteUrl: websiteSchema,
  organizationSize: z.enum(ORGANIZATION_SIZE_OPTIONS, {
    error: "Please select a valid organization size",
  }),
  companyEmailDomain: z
    .string()
    .trim()
    .toLowerCase()
    .min(3, "Company email domain is required")
    .max(253, "Company email domain cannot exceed 253 characters")
    .regex(domainPattern, "Enter a valid domain, for example yourcompany.com"),
  logoUrl: z.string().trim().max(500, "Logo URL cannot exceed 500 characters").optional(),
  description: z
    .string()
    .trim()
    .max(250, "Description cannot exceed 250 characters")
    .optional(),
});

export const emailVolumeStepSchema = z.object({
  emailVolume: z.enum(EMAIL_VOLUME_OPTIONS, {
    error: "Please select a valid monthly email volume",
  }),
});

export const industrySectorStepSchema = z.object({
  industrySector: z.enum(INDUSTRY_OPTIONS, {
    error: "Please select a valid industry sector",
  }),
});

export const sourceStepSchema = z.object({
  source: z.enum(SOURCE_OPTIONS, {
    error: "Please select how you heard about MailTracko",
  }),
});

export const themeStepSchema = z.object({
  theme: z.enum(["light", "dark"], {
    error: "Please select Light or Dark theme",
  }),
});

export type OrganizationStepFormInput = z.input<typeof organizationStepSchema>;
export type OrganizationStepFormData = z.output<typeof organizationStepSchema>;
export type EmailVolumeFormData = z.infer<typeof emailVolumeStepSchema>;
export type IndustrySectorFormData = z.infer<typeof industrySectorStepSchema>;
export type SourceStepFormData = z.infer<typeof sourceStepSchema>;
export type ThemeStepFormData = z.infer<typeof themeStepSchema>;
