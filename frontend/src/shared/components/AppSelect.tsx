import { useEffect, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Search } from "lucide-react";

export interface AppSelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface AppSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  options: AppSelectOption[];
  ariaLabel: string;
  placeholder?: string;
  disabled?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  className?: string;
  triggerClassName?: string;
  placement?: "auto" | "top" | "bottom";
}

export function AppSelect({
  value,
  onValueChange,
  options,
  ariaLabel,
  placeholder = "Select an option",
  disabled = false,
  searchable = false,
  searchPlaceholder = "Search…",
  className = "",
  triggerClassName = "",
  placement = "auto",
}: AppSelectProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [resolvedPlacement, setResolvedPlacement] = useState<"top" | "bottom">("bottom");
  const rootRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const filteredOptions = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return options;
    return options.filter((option) => option.label.toLowerCase().includes(query));
  }, [options, search]);

  const selected = options.find((option) => option.value === value);

  useEffect(() => {
    if (!open || !rootRef.current) return;
    const rect = rootRef.current.getBoundingClientRect();
    const estimatedMenuHeight = Math.min(320, 24 + filteredOptions.length * 42 + (searchable ? 48 : 0));
    const spaceAbove = rect.top - 12;
    const spaceBelow = window.innerHeight - rect.bottom - 12;

    if (placement === "top") {
      setResolvedPlacement(spaceAbove >= Math.min(estimatedMenuHeight, 180) || spaceAbove >= spaceBelow ? "top" : "bottom");
    } else if (placement === "bottom") {
      setResolvedPlacement(spaceBelow >= Math.min(estimatedMenuHeight, 180) || spaceBelow >= spaceAbove ? "bottom" : "top");
    } else {
      setResolvedPlacement(spaceBelow >= estimatedMenuHeight || spaceBelow >= spaceAbove ? "bottom" : "top");
    }
  }, [open, placement, searchable, filteredOptions.length]);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [open]);

  useEffect(() => {
    if (!open) {
      setSearch("");
      return;
    }
    const selectedIndex = filteredOptions.findIndex((option) => option.value === value && !option.disabled);
    const nextIndex = selectedIndex >= 0 ? selectedIndex : Math.max(0, filteredOptions.findIndex((option) => !option.disabled));
    setActiveIndex(nextIndex);
    window.setTimeout(() => {
      if (searchable) searchRef.current?.focus();
      else optionRefs.current[nextIndex]?.focus();
    }, 0);
  }, [open, searchable, value]); // filtered list updates are handled by keyboard/search effect below

  useEffect(() => {
    if (!open || !searchable) return;
    const firstEnabled = filteredOptions.findIndex((option) => !option.disabled);
    setActiveIndex(Math.max(0, firstEnabled));
  }, [filteredOptions, open, searchable]);

  const selectOption = (option: AppSelectOption) => {
    if (option.disabled) return;
    onValueChange(option.value);
    setOpen(false);
  };

  const move = (direction: 1 | -1) => {
    if (!filteredOptions.length) return;
    let index = activeIndex;
    for (let i = 0; i < filteredOptions.length; i += 1) {
      index = (index + direction + filteredOptions.length) % filteredOptions.length;
      if (!filteredOptions[index]?.disabled) {
        setActiveIndex(index);
        optionRefs.current[index]?.focus();
        break;
      }
    }
  };

  return (
    <div ref={rootRef} className={`relative ${className}`}>
      <button
        type="button"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={(event) => {
          if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
            event.preventDefault();
            setOpen(true);
          }
        }}
        className={`flex min-h-10 w-full items-center justify-between gap-3 rounded-xl border border-[#CEC6B0]/60 bg-white px-3 py-2 text-left text-sm text-[#1A1C1C] shadow-sm transition hover:border-[#B8AD90] focus:outline-none focus:ring-1 focus:ring-[#F1D442]/30 disabled:cursor-not-allowed disabled:opacity-50 ${triggerClassName}`}
      >
        <span className={`min-w-0 flex-1 truncate ${selected ? "" : "text-[#756F60]"}`}>
          {selected?.label ?? placeholder}
        </span>
        <ChevronDown className={`h-4 w-4 shrink-0 text-[#756F60] transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open ? (
        <div
          className={`absolute left-0 z-[80] w-full min-w-[180px] overflow-hidden rounded-xl border border-[#CEC6B0]/50 bg-white shadow-xl ${
            resolvedPlacement === "top"
              ? "bottom-full top-auto mb-1.5"
              : "top-full bottom-auto mt-1.5"
          }`}
        >
          {searchable ? (
            <div className="flex items-center gap-2 border-b border-[#EEE9DC] bg-[#FBFAF6] px-3 py-2">
              <Search className="h-4 w-4 shrink-0 text-[#756F60]" />
              <input
                ref={searchRef}
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Escape") {
                    event.preventDefault();
                    setOpen(false);
                  } else if (event.key === "ArrowDown") {
                    event.preventDefault();
                    move(1);
                  } else if (event.key === "ArrowUp") {
                    event.preventDefault();
                    move(-1);
                  } else if (event.key === "Enter") {
                    event.preventDefault();
                    const option = filteredOptions[activeIndex];
                    if (option) selectOption(option);
                  }
                }}
                placeholder={searchPlaceholder}
                className="min-w-0 flex-1 border-0 bg-transparent p-0 text-sm outline-none ring-0"
              />
            </div>
          ) : null}

          <div role="listbox" aria-label={ariaLabel} className="max-h-64 overflow-y-auto p-1.5">
            {filteredOptions.length ? filteredOptions.map((option, index) => (
              <button
                key={option.value}
                ref={(node) => { optionRefs.current[index] = node; }}
                type="button"
                role="option"
                aria-selected={option.value === value}
                disabled={option.disabled}
                tabIndex={searchable ? -1 : index === activeIndex ? 0 : -1}
                onFocus={() => setActiveIndex(index)}
                onClick={() => selectOption(option)}
                onKeyDown={(event) => {
                  if (event.key === "Escape") {
                    event.preventDefault();
                    setOpen(false);
                  } else if (event.key === "ArrowDown") {
                    event.preventDefault();
                    move(1);
                  } else if (event.key === "ArrowUp") {
                    event.preventDefault();
                    move(-1);
                  } else if (event.key === "Home") {
                    event.preventDefault();
                    const first = filteredOptions.findIndex((item) => !item.disabled);
                    if (first >= 0) {
                      setActiveIndex(first);
                      optionRefs.current[first]?.focus();
                    }
                  } else if (event.key === "End") {
                    event.preventDefault();
                    const last = [...filteredOptions].map((item) => !item.disabled).lastIndexOf(true);
                    if (last >= 0) {
                      setActiveIndex(last);
                      optionRefs.current[last]?.focus();
                    }
                  }
                }}
                className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm transition disabled:cursor-not-allowed disabled:opacity-40 ${
                  option.value === value
                    ? "bg-[#F5E29F]/40 font-semibold text-[#6E5E00]"
                    : "text-[#1A1C1C] hover:bg-[#F4F3F3] focus:bg-[#F4F3F3]"
                }`}
              >
                <span className="min-w-0 flex-1 truncate">{option.label}</span>
                {option.value === value ? <Check className="h-4 w-4 shrink-0 text-[#8F740D]" /> : null}
              </button>
            )) : (
              <p className="px-3 py-5 text-center text-xs text-[#756F60]">No options found</p>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
