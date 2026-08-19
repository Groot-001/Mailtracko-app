import { z } from "zod";

const hostSchema = z
  .string()
  .trim()
  .min(1, "Host is required.")
  .max(253, "Host cannot exceed 253 characters.")
  .refine((value) => !/\s/.test(value) && !value.includes("://"), "Enter a hostname such as smtp.example.com.");

const portSchema = z
  .string()
  .trim()
  .min(1, "Port is required.")
  .regex(/^\d+$/, "Port must contain numbers only.")
  .refine((value) => {
    const port = Number(value);
    return Number.isInteger(port) && port >= 1 && port <= 65535;
  }, "Port must be between 1 and 65535.");

export const smtpFormSchema = z
  .object({
    sender_name: z
      .string()
      .trim()
      .max(50, "Sender name cannot exceed 50 characters.")
      .refine((value) => !value || /[A-Za-z]/.test(value), "Sender name must contain at least one letter."),
    email: z.string().trim().min(1, "Email address is required.").email("Enter a valid email address.").max(254, "Email address is too long."),
    smtp_host: hostSchema,
    smtp_port: portSchema,
    smtp_username: z.string().trim().min(1, "SMTP username is required.").max(255, "SMTP username is too long."),
    smtp_password: z.string().min(1, "SMTP password is required.").max(255, "SMTP password is too long."),
    imap_host: z.string().trim().max(253, "IMAP host cannot exceed 253 characters."),
    imap_port: z.string().trim(),
  })
  .superRefine((values, ctx) => {
    if (values.imap_host) {
      if (/\s/.test(values.imap_host) || values.imap_host.includes("://")) {
        ctx.addIssue({ code: "custom", path: ["imap_host"], message: "Enter a hostname such as imap.example.com." });
      }
      const portResult = portSchema.safeParse(values.imap_port);
      if (!portResult.success) {
        ctx.addIssue({ code: "custom", path: ["imap_port"], message: portResult.error.issues[0]?.message ?? "Enter a valid IMAP port." });
      }
    } else if (values.imap_port && values.imap_port !== "993") {
      ctx.addIssue({ code: "custom", path: ["imap_host"], message: "Enter an IMAP host to use a custom IMAP port." });
    }
  });

export type SmtpFormValues = z.infer<typeof smtpFormSchema>;

export const normalizePort = (value: string) => value.replace(/\D/g, "").replace(/^0+(?=\d)/, "");
