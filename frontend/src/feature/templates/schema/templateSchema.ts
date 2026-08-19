import { z } from "zod";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const hasVisibleContent = (html: string) => {
  const text = html
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;|&#160;/gi, " ")
    .replace(/&[a-z0-9#]+;/gi, " ")
    .trim();
  return text.length > 0 || /<img\b[^>]*\bsrc\s*=\s*["'][^"']+["'][^>]*>/i.test(html);
};

export const templateDraftSchema = z.object({
  name: z.string().trim().min(1, "Template name is required.").max(50, "Template name cannot exceed 50 characters."),
  subject: z.string().trim().min(1, "Subject line is required.").max(255, "Subject line cannot exceed 255 characters."),
  body_html: z
    .string()
    .max(200_000, "Email body is too large.")
    .refine(hasVisibleContent, "Email body cannot be empty."),
  description: z.string().max(500, "Description cannot exceed 500 characters."),
  preheader: z.string().max(255, "Preview text cannot exceed 255 characters."),
  from_name: z
    .string()
    .max(50, "From Name cannot exceed 50 characters.")
    .refine((value) => !value.trim() || /[A-Za-z]/.test(value), "From Name must contain at least one letter."),
  from_email: z
    .string()
    .max(50, "From Email cannot exceed 50 characters.")
    .refine((value) => !value.trim() || EMAIL_RE.test(value.trim()), "Enter a valid From Email address."),
  category_id: z.number().int().positive().nullable(),
  tags: z
    .array(z.string().trim().min(1, "Tags cannot be empty.").max(50, "Each template tag cannot exceed 50 characters."))
    .max(20, "A template cannot contain more than 20 tags."),
  is_default: z.boolean(),
});

export const templateContentSchema = templateDraftSchema.pick({
  name: true,
  subject: true,
  body_html: true,
  preheader: true,
});

export const templateSettingsSchema = templateDraftSchema.pick({
  description: true,
  from_name: true,
  from_email: true,
  category_id: true,
  tags: true,
  is_default: true,
});

export type TemplateFieldErrors = Record<string, string>;

export const getTemplateFieldErrors = (
  result: ReturnType<typeof templateDraftSchema.safeParse> | ReturnType<typeof templateContentSchema.safeParse> | ReturnType<typeof templateSettingsSchema.safeParse>,
): TemplateFieldErrors => {
  if (result.success) return {};
  const errors: TemplateFieldErrors = {};
  for (const issue of result.error.issues) {
    const field = String(issue.path[0] ?? "form");
    if (!errors[field]) errors[field] = issue.message;
  }
  return errors;
};
