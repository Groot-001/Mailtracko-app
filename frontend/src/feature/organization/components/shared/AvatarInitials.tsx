interface AvatarInitialsProps {
  name: string | null | undefined;
  email?: string | null;
  avatarUrl?: string | null;
  bgColor?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "w-7 h-7 text-xs",
  md: "w-9 h-9 text-sm",
  lg: "w-11 h-11 text-base",
};

/**
 * Derives display initials from a name or email.
 * Falls back to the first character of the email local part.
 */
function getInitials(name?: string | null, email?: string | null): string {
  if (name) {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return parts[0].slice(0, 2).toUpperCase();
  }
  if (email) {
    return email[0].toUpperCase();
  }
  return "?";
}

export const AvatarInitials = ({
  name,
  email,
  avatarUrl,
  bgColor,
  size = "md",
  className = "",
}: AvatarInitialsProps) => {
  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={name ?? email ?? "avatar"}
        className={`${sizeClasses[size]} rounded-full object-cover flex-shrink-0 ${className}`}
      />
    );
  }

  const initials = getInitials(name, email);
  const bg = bgColor ?? "#8F740D";

  return (
    <span
      className={`${sizeClasses[size]} rounded-full flex items-center justify-center font-semibold text-white flex-shrink-0 select-none ${className}`}
      style={{ backgroundColor: bg }}
      aria-label={name ?? email ?? "user avatar"}
    >
      {initials}
    </span>
  );
};
