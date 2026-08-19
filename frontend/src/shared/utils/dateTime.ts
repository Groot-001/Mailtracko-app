const parseLocalDateTime = (value: string) => {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(value);
  if (!match) return null;

  const [, year, month, day, hour, minute, second = "0"] = match;
  return {
    year: Number(year),
    month: Number(month),
    day: Number(day),
    hour: Number(hour),
    minute: Number(minute),
    second: Number(second),
  };
};

const dateTimePartsAt = (timestamp: number, timeZone: string) => {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date(timestamp));

  const values = Object.fromEntries(
    parts
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, Number(part.value)]),
  );

  return {
    year: values.year,
    month: values.month,
    day: values.day,
    hour: values.hour,
    minute: values.minute,
    second: values.second,
  };
};

const timeZoneOffsetAt = (timestamp: number, timeZone: string) => {
  const parts = dateTimePartsAt(timestamp, timeZone);
  const representedAsUtc = Date.UTC(
    parts.year,
    parts.month - 1,
    parts.day,
    parts.hour,
    parts.minute,
    parts.second,
  );

  return representedAsUtc - timestamp;
};

/** Converts a datetime-local value in an IANA timezone into an offset-aware ISO timestamp. */
export const zonedLocalDateTimeToIso = (value: string, timeZone: string): string | null => {
  const parsed = parseLocalDateTime(value);
  if (!parsed) return null;

  try {
    const desiredAsUtc = Date.UTC(
      parsed.year,
      parsed.month - 1,
      parsed.day,
      parsed.hour,
      parsed.minute,
      parsed.second,
    );

    let utcTimestamp = desiredAsUtc - timeZoneOffsetAt(desiredAsUtc, timeZone);
    // Recalculate once at the resolved instant to account for daylight-saving boundaries.
    utcTimestamp = desiredAsUtc - timeZoneOffsetAt(utcTimestamp, timeZone);

    const date = new Date(utcTimestamp);
    if (Number.isNaN(date.getTime())) return null;

    // Reject nonexistent wall-clock times during daylight-saving transitions.
    const resolved = dateTimePartsAt(utcTimestamp, timeZone);
    if (
      resolved.year !== parsed.year ||
      resolved.month !== parsed.month ||
      resolved.day !== parsed.day ||
      resolved.hour !== parsed.hour ||
      resolved.minute !== parsed.minute ||
      resolved.second !== parsed.second
    ) {
      return null;
    }

    return date.toISOString();
  } catch {
    return null;
  }
};
