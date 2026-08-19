interface ToggleSwitchProps {
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  label?: string;
  srLabel?: string;
}

/**
 * Accessible iOS-style toggle switch.
 * Uses a visually-hidden checkbox for full keyboard + screen-reader support.
 */
export const ToggleSwitch = ({
  id,
  checked,
  onChange,
  disabled = false,
  label,
  srLabel,
}: ToggleSwitchProps) => {
  return (
    <label
      htmlFor={id}
      className={`relative inline-flex items-center gap-2 ${disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer"}`}
    >
      {label && (
        <span className="text-sm text-[#1A1C1C]">{label}</span>
      )}
      <span className="relative">
        <input
          id={id}
          type="checkbox"
          role="switch"
          aria-checked={checked}
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="sr-only"
        />
        {srLabel && <span className="sr-only">{srLabel}</span>}
        {/* Track */}
        <span
          className={`block w-11 h-6 rounded-full transition-colors duration-200 ease-in-out ${
            checked ? "bg-[#8F740D]" : "bg-[#CEC6B0]"
          }`}
        />
        {/* Thumb */}
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200 ease-in-out ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </span>
    </label>
  );
};
