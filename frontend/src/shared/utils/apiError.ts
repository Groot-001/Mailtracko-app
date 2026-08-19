import axios from "axios";

type ApiErrorPayload = {
  error?: string;
  message?: string;
  detail?: unknown;
  errors?: unknown;
};

const humanizeField = (field: string) => {
  const leaf = field.split(".").filter(Boolean).at(-1) || field;
  return leaf
    .replace(/\[(\d+)\]/g, " $1")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
};

const cleanValidationMessage = (message: string) =>
  message
    .replace(/^Value error,\s*/i, "")
    .replace(/^Assertion failed,\s*/i, "")
    .trim();

const firstStructuredError = (errors: unknown): string | undefined => {
  if (!errors) return undefined;

  if (typeof errors === "string") return cleanValidationMessage(errors);

  if (Array.isArray(errors)) {
    for (const item of errors) {
      if (typeof item === "string" && item.trim()) return cleanValidationMessage(item);
      if (item && typeof item === "object") {
        const entry = item as { msg?: string; message?: string; loc?: Array<string | number> };
        const message = entry.message || entry.msg;
        if (message) {
          const field = entry.loc?.filter((part) => part !== "body").join(".");
          return field ? `${humanizeField(field)}: ${cleanValidationMessage(message)}` : cleanValidationMessage(message);
        }
      }
    }
    return undefined;
  }

  if (typeof errors === "object") {
    for (const [field, value] of Object.entries(errors as Record<string, unknown>)) {
      const nested = firstStructuredError(value);
      if (nested) return `${humanizeField(field)}: ${nested}`;
    }
  }

  return undefined;
};

const appendFieldErrors = (
  value: unknown,
  target: Record<string, string>,
  prefix = "",
) => {
  if (!value) return;

  if (typeof value === "string") {
    if (prefix && !target[prefix]) target[prefix] = cleanValidationMessage(value);
    return;
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      if (item && typeof item === "object") {
        const entry = item as { msg?: string; message?: string; loc?: Array<string | number> };
        const message = entry.message || entry.msg;
        const path = entry.loc?.filter((part) => part !== "body").map(String).join(".") || prefix;
        if (message && path && !target[path]) target[path] = cleanValidationMessage(message);
      } else if (typeof item === "string" && prefix && !target[prefix]) {
        target[prefix] = cleanValidationMessage(item);
      }
    }
    return;
  }

  if (typeof value === "object") {
    for (const [key, nested] of Object.entries(value as Record<string, unknown>)) {
      const path = prefix ? `${prefix}.${key}` : key;
      appendFieldErrors(nested, target, path);
    }
  }
};

/**
 * Returns backend validation messages keyed by request field path. This lets
 * forms attach server-authoritative validation to the same fields as Zod/RHF
 * instead of showing a generic toast such as "Validation Error".
 */
export const getApiFieldErrors = (error: unknown): Record<string, string> => {
  if (!axios.isAxiosError(error)) return {};
  const responseData = error.response?.data as ApiErrorPayload | undefined;
  const result: Record<string, string> = {};
  appendFieldErrors(responseData?.errors, result);
  if (Array.isArray(responseData?.detail)) appendFieldErrors(responseData.detail, result);
  return result;
};

export const getApiErrorMessage = (error: unknown, fallback: string) => {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data as ApiErrorPayload | undefined;

    const structured = firstStructuredError(responseData?.errors);
    if (structured) return structured;

    if (Array.isArray(responseData?.detail)) {
      const detail = firstStructuredError(responseData.detail);
      if (detail) return detail;
    }

    if (typeof responseData?.detail === "string" && responseData.detail.trim()) {
      return cleanValidationMessage(responseData.detail);
    }

    const generic = responseData?.error || responseData?.message;
    if (generic && generic.toLowerCase() !== "validation error") return generic;

    return fallback || generic || "The request could not be completed.";
  }
  return error instanceof Error ? error.message : fallback;
};
