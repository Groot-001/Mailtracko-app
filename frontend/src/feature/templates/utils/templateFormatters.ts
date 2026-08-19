export const formatTemplateDate = (value: string | null) => {
  if (!value) return "Not updated yet";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown date";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

export const statusLabel = (status: string) =>
  status.charAt(0).toUpperCase() + status.slice(1).replaceAll("_", " ");
