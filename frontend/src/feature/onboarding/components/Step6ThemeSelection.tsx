import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Check, Moon, Sun } from "lucide-react";
import type { ThemeOption } from "../types/onboarding.types";
import {
  themeStepSchema,
  type ThemeStepFormData,
  type ThemeStepFormInput,
} from "../schema/onboardingSchema";

interface Step6ThemeSelectionProps {
  initialTheme: ThemeOption;
  onNext: (theme: ThemeOption) => void;
  onBack: () => void;
}

const THEMES: Array<{
  id: ThemeOption;
  name: string;
  description: string;
  icon: typeof Sun;
}> = [
  {
    id: "light",
    name: "Light",
    description: "Bright, clean surfaces for daytime work and maximum readability.",
    icon: Sun,
  },
  {
    id: "dark",
    name: "Dark",
    description: "Low-light surfaces designed for comfortable focused work.",
    icon: Moon,
  },
];

export function Step6ThemeSelection({
  initialTheme,
  onNext,
  onBack,
}: Step6ThemeSelectionProps) {
  const {
    handleSubmit,
    control,
    setValue,
    formState: { errors },
  } = useForm<ThemeStepFormInput, unknown, ThemeStepFormData>({
    resolver: zodResolver(themeStepSchema),
    defaultValues: {
      theme: initialTheme,
    },
  });

  const selectedTheme = useWatch({ control, name: "theme" });

  const onSubmit = (data: ThemeStepFormData) => {
    onNext(data.theme);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="w-full space-y-8 rounded-2xl border border-[#CEC6B0]/40 bg-white p-6 shadow-lg sm:p-10">
      <div className="space-y-2">
        <div className="inline-block rounded-full border border-[#F2DF9C] bg-[#F5E29F]/50 px-3 py-1 text-xs font-semibold text-[#8F740D]">
          Step 6 of 7
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-[#1A1C1C] sm:text-4xl">
          Choose your workspace theme
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-[#4C4736]">
          MailTracko supports two application themes. Your choice is saved consistently in your workspace and account preferences.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-2" role="radiogroup" aria-label="Workspace theme">
        {THEMES.map((theme) => {
          const selected = selectedTheme === theme.id;
          const Icon = theme.icon;
          const dark = theme.id === "dark";
          return (
            <button
              key={theme.id}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => setValue("theme", theme.id, { shouldValidate: true })}
              className={`relative overflow-hidden rounded-2xl border-2 p-5 text-left transition ${
                selected
                  ? "border-[#8F740D] ring-2 ring-[#8F740D]/20"
                  : "border-[#CEC6B0]/50 hover:border-[#8F740D]/60"
              }`}
            >
              {selected && (
                <span className="absolute right-4 top-4 grid h-7 w-7 place-items-center rounded-full bg-[#8F740D] text-white">
                  <Check className="h-4 w-4" />
                </span>
              )}

              <div className={`rounded-xl border p-4 ${dark ? "border-slate-700 bg-slate-950" : "border-stone-200 bg-stone-50"}`}>
                <div className="flex gap-3">
                  <div className={`h-24 w-16 rounded-lg ${dark ? "bg-slate-800" : "bg-white"}`} />
                  <div className="flex-1 space-y-3">
                    <div className={`h-4 w-24 rounded ${dark ? "bg-slate-700" : "bg-stone-300"}`} />
                    <div className="grid grid-cols-2 gap-2">
                      <div className={`h-14 rounded-lg ${dark ? "bg-slate-800" : "bg-white"}`} />
                      <div className={`h-14 rounded-lg ${dark ? "bg-slate-800" : "bg-white"}`} />
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-start gap-3">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#F5E29F]/40 text-[#8F740D]">
                  <Icon className="h-5 w-5" />
                </span>
                <div>
                  <h2 className="text-sm font-bold text-[#1A1C1C]">{theme.name}</h2>
                  <p className="mt-1 text-xs leading-5 text-[#4C4736]">{theme.description}</p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {errors.theme && <p role="alert" className="text-sm font-medium text-red-600">{errors.theme.message}</p>}

      <div className="flex items-center justify-between border-t border-[#EEEEEE] pt-6">
        <button
          type="button"
          onClick={onBack}
          className="rounded-xl border border-[#CEC6B0] px-6 py-3 text-sm font-semibold text-[#4C4736] transition hover:bg-[#EEEEEE]"
        >
          Back
        </button>
        <button
          type="submit"
          className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-8 py-3 text-sm font-bold text-white shadow-md transition hover:bg-[#6E5E00]"
        >
          Continue <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </form>
  );
}
