import { useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BadgeCheck,
  CircleDollarSign,
  KeyRound,
  Loader2,
  Pencil,
  Plus,
  Save,
  Webhook,
  X,
} from "lucide-react";

import type {
  AdminBillingPlan,
  AdminBillingPlanPayload,
} from "../api/platformApi";
import {
  createAdminPlan,
  getAdminBillingConfiguration,
  getAdminPlans,
  updateAdminPlan,
} from "../api/platformApi";

type PlanForm = Omit<AdminBillingPlanPayload, "limits" | "features"> & {
  limitsText: string;
  featuresText: string;
};

const emptyPlan = (): PlanForm => ({
  code: "",
  name: "",
  description: "",
  currency: "USD",
  monthly_price_cents: 0,
  annual_price_cents: 0,
  stripe_monthly_price_id: "",
  stripe_annual_price_id: "",
  trial_days: 0,
  limitsText: "{}",
  featuresText: "",
  is_active: true,
  is_default: false,
  display_order: 0,
});

const toForm = (plan: AdminBillingPlan): PlanForm => ({
  ...plan,
  description: plan.description || "",
  stripe_monthly_price_id: plan.stripe_monthly_price_id || "",
  stripe_annual_price_id: plan.stripe_annual_price_id || "",
  limitsText: JSON.stringify(plan.limits || {}, null, 2),
  featuresText: (plan.features || []).join("\n"),
});

const parseLimits = (value: string) => {
  const limits = JSON.parse(value || "{}") as unknown;
  if (!limits || Array.isArray(limits) || typeof limits !== "object") {
    throw new Error("Limits must be a JSON object.");
  }
  for (const [key, amount] of Object.entries(limits)) {
    if (!key.trim() || !Number.isInteger(amount) || Number(amount) < 0) {
      throw new Error("Every limit must have a name and a non-negative integer value.");
    }
  }
  return limits as Record<string, number>;
};

const errorMessage = (error: unknown) => {
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === "object" && error && "response" in error) {
    const response = (error as { response?: { data?: { message?: string } } }).response;
    return response?.data?.message || "The billing plan could not be saved.";
  }
  return "The billing plan could not be saved.";
};

const fieldClass =
  "mt-1 w-full rounded-xl border border-[#CEC6B0]/70 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-[#8F740D] focus:ring-2 focus:ring-[#F1D442]/25";

export function StripeAdminPanel() {
  const queryClient = useQueryClient();
  const [editingUuid, setEditingUuid] = useState<string | null>(null);
  const [form, setForm] = useState<PlanForm>(emptyPlan);
  const [validationError, setValidationError] = useState<string | null>(null);
  const configuration = useQuery({
    queryKey: ["admin", "billing", "configuration"],
    queryFn: getAdminBillingConfiguration,
  });
  const plans = useQuery({ queryKey: ["admin", "plans"], queryFn: getAdminPlans });
  const savePlan = useMutation({
    mutationFn: (values: AdminBillingPlanPayload) =>
      editingUuid
        ? updateAdminPlan({ uuid: editingUuid, values })
        : createAdminPlan(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "plans"] });
      queryClient.invalidateQueries({ queryKey: ["billing", "overview"] });
      setEditingUuid(null);
      setForm(emptyPlan());
      setValidationError(null);
    },
  });

  const configuredPriceCount = useMemo(
    () =>
      (plans.data?.items || []).reduce(
        (total, plan) =>
          total + Number(Boolean(plan.stripe_monthly_price_id)) + Number(Boolean(plan.stripe_annual_price_id)),
        0,
      ),
    [plans.data],
  );

  const set = <K extends keyof PlanForm>(key: K, value: PlanForm[K]) =>
    setForm((current) => ({ ...current, [key]: value }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    try {
      const limits = parseLimits(form.limitsText);
      const features = form.featuresText
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean);
      setValidationError(null);
      savePlan.mutate({
        code: form.code.trim(),
        name: form.name.trim(),
        description: form.description?.trim() || null,
        currency: form.currency.trim().toUpperCase(),
        monthly_price_cents: Number(form.monthly_price_cents),
        annual_price_cents: Number(form.annual_price_cents),
        stripe_monthly_price_id: form.stripe_monthly_price_id?.trim() || null,
        stripe_annual_price_id: form.stripe_annual_price_id?.trim() || null,
        trial_days: Number(form.trial_days),
        limits,
        features,
        is_active: form.is_active,
        is_default: form.is_default,
        display_order: Number(form.display_order),
      });
    } catch (error) {
      setValidationError(errorMessage(error));
    }
  };

  const startEdit = (plan: AdminBillingPlan) => {
    setEditingUuid(plan.uuid);
    setForm(toForm(plan));
    setValidationError(null);
  };

  const cancelEdit = () => {
    setEditingUuid(null);
    setForm(emptyPlan());
    setValidationError(null);
  };

  const config = configuration.data;
  const ready = Boolean(
    config?.billing_enabled && config.secret_key_configured && config.webhook_secret_configured,
  );

  return (
    <section className="space-y-5 rounded-2xl border border-[#CEC6B0]/50 bg-white p-5">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-[#8F740D]">
            <CircleDollarSign className="h-5 w-5" />
            <p className="text-[11px] font-bold uppercase tracking-[0.16em]">Stripe billing</p>
          </div>
          <h2 className="mt-2 font-bold text-[#1A1C1C]">Provider readiness and recurring plans</h2>
          <p className="mt-1 max-w-2xl text-xs text-[#756F60]">
            Credentials stay in server environment variables. This panel only reports readiness and stores Stripe Price IDs on billing plans.
          </p>
        </div>
        {configuration.isLoading ? (
          <Loader2 className="h-5 w-5 animate-spin text-[#8F740D]" />
        ) : (
          <span
            className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider ${
              ready ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800"
            }`}
          >
            {ready ? `${config?.mode} mode ready` : "Configuration required"}
          </span>
        )}
      </header>

      {config && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <StatusCard icon={KeyRound} label="Secret key" ready={config.secret_key_configured} detail={config.mode} />
          <StatusCard icon={Webhook} label="Webhook signing" ready={config.webhook_secret_configured} detail={config.webhook_path} />
          <StatusCard icon={BadgeCheck} label="Billing switch" ready={config.billing_enabled} detail={config.billing_enabled ? "Enabled" : "Disabled"} />
          <StatusCard icon={CircleDollarSign} label="Configured prices" ready={configuredPriceCount > 0} detail={`${configuredPriceCount} recurring Price IDs`} />
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-[1.05fr_1.4fr]">
        <form onSubmit={submit} className="rounded-2xl border border-[#EEE9DC] bg-[#FBFAF6] p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold">{editingUuid ? "Edit recurring plan" : "Add recurring plan"}</h3>
              <p className="mt-1 text-[11px] text-[#756F60]">Prices are stored in the smallest currency unit.</p>
            </div>
            {editingUuid ? (
              <button type="button" onClick={cancelEdit} className="rounded-lg border border-[#CEC6B0] p-2" aria-label="Cancel plan edit">
                <X className="h-4 w-4" />
              </button>
            ) : (
              <Plus className="h-5 w-5 text-[#8F740D]" />
            )}
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <Field label="Plan code"><input required pattern="[a-z0-9]+(?:_[a-z0-9]+)*" value={form.code} onChange={(event) => set("code", event.target.value)} className={fieldClass} placeholder="business" /></Field>
            <Field label="Plan name"><input required value={form.name} onChange={(event) => set("name", event.target.value)} className={fieldClass} placeholder="Business" /></Field>
            <Field label="Currency"><input required minLength={3} maxLength={3} value={form.currency} onChange={(event) => set("currency", event.target.value)} className={fieldClass} /></Field>
            <Field label="Display order"><input required min={0} type="number" value={form.display_order} onChange={(event) => set("display_order", Number(event.target.value))} className={fieldClass} /></Field>
            <Field label="Monthly price (cents)"><input required min={0} type="number" value={form.monthly_price_cents} onChange={(event) => set("monthly_price_cents", Number(event.target.value))} className={fieldClass} /></Field>
            <Field label="Annual price (cents)"><input required min={0} type="number" value={form.annual_price_cents} onChange={(event) => set("annual_price_cents", Number(event.target.value))} className={fieldClass} /></Field>
            <Field label="Monthly Stripe Price ID"><input value={form.stripe_monthly_price_id || ""} onChange={(event) => set("stripe_monthly_price_id", event.target.value)} className={fieldClass} placeholder="price_…" /></Field>
            <Field label="Annual Stripe Price ID"><input value={form.stripe_annual_price_id || ""} onChange={(event) => set("stripe_annual_price_id", event.target.value)} className={fieldClass} placeholder="price_…" /></Field>
            <Field label="Trial days"><input required min={0} max={365} type="number" value={form.trial_days} onChange={(event) => set("trial_days", Number(event.target.value))} className={fieldClass} /></Field>
          </div>
          <Field label="Description"><textarea value={form.description || ""} onChange={(event) => set("description", event.target.value)} className={`${fieldClass} min-h-20 resize-y`} /></Field>
          <Field label="Limits (JSON)"><textarea required value={form.limitsText} onChange={(event) => set("limitsText", event.target.value)} className={`${fieldClass} min-h-28 resize-y font-mono text-xs`} spellCheck={false} /></Field>
          <Field label="Features (one per line)"><textarea value={form.featuresText} onChange={(event) => set("featuresText", event.target.value)} className={`${fieldClass} min-h-24 resize-y`} /></Field>
          <div className="mt-4 flex flex-wrap gap-4 text-xs">
            <label className="flex items-center gap-2"><input type="checkbox" checked={form.is_active} onChange={(event) => set("is_active", event.target.checked)} />Active</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={form.is_default} onChange={(event) => set("is_default", event.target.checked)} />Default workspace plan</label>
          </div>
          {(validationError || savePlan.error) && <p className="mt-3 rounded-lg bg-red-50 p-3 text-xs text-red-700">{validationError || errorMessage(savePlan.error)}</p>}
          <button disabled={savePlan.isPending} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#1A1C1C] px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50">
            {savePlan.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {editingUuid ? "Save plan changes" : "Create plan"}
          </button>
        </form>

        <div className="overflow-hidden rounded-2xl border border-[#EEE9DC]">
          <header className="border-b border-[#EEE9DC] bg-[#FBFAF6] p-4">
            <h3 className="text-sm font-bold">Configured plans</h3>
            <p className="mt-1 text-[11px] text-[#756F60]">Checkout is available only for cycles with a valid Stripe Price ID.</p>
          </header>
          {plans.isLoading ? (
            <Loader2 className="m-6 h-5 w-5 animate-spin text-[#8F740D]" />
          ) : (
            <div className="divide-y divide-[#F4F1E8]">
              {plans.data?.items.map((plan) => (
                <article key={plan.uuid} className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="font-semibold text-[#1A1C1C]">{plan.name}</h4>
                        <span className="rounded-full bg-[#F7F4E8] px-2 py-0.5 text-[10px] font-semibold text-[#594C05]">{plan.code}</span>
                        {plan.is_default && <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700">Default</span>}
                        {!plan.is_active && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">Inactive</span>}
                      </div>
                      <p className="mt-1 text-xs text-[#756F60]">{plan.currency} {(plan.monthly_price_cents / 100).toFixed(2)} monthly · {(plan.annual_price_cents / 100).toFixed(2)} annually</p>
                    </div>
                    <button type="button" onClick={() => startEdit(plan)} className="rounded-lg border border-[#CEC6B0] p-2 text-[#594C05]" aria-label={`Edit ${plan.name}`}><Pencil className="h-4 w-4" /></button>
                  </div>
                  <dl className="mt-3 grid gap-2 text-[11px] sm:grid-cols-2">
                    <PriceStatus label="Monthly" value={plan.stripe_monthly_price_id} />
                    <PriceStatus label="Annual" value={plan.stripe_annual_price_id} />
                  </dl>
                </article>
              ))}
              {!plans.data?.items.length && <p className="p-8 text-center text-sm text-[#756F60]">No billing plans are configured.</p>}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="mt-3 block text-[11px] font-semibold text-[#4C4736]">{label}{children}</label>;
}

function StatusCard({ icon: Icon, label, ready, detail }: { icon: typeof KeyRound; label: string; ready: boolean; detail: string }) {
  return <div className="flex items-start gap-3 rounded-xl border border-[#EEE9DC] bg-[#FBFAF6] p-3"><Icon className={`mt-0.5 h-4 w-4 ${ready ? "text-emerald-600" : "text-amber-700"}`} /><div className="min-w-0"><p className="text-[10px] font-bold uppercase tracking-wider text-[#756F60]">{label}</p><p className="mt-1 truncate text-xs font-semibold">{ready ? "Configured" : "Required"}</p><p className="mt-0.5 truncate text-[10px] text-[#756F60]">{detail}</p></div></div>;
}

function PriceStatus({ label, value }: { label: string; value?: string | null }) {
  return <div className="rounded-lg bg-[#FBFAF6] px-3 py-2"><dt className="font-semibold text-[#756F60]">{label}</dt><dd className={`mt-1 break-all font-mono text-[10px] ${value ? "text-emerald-700" : "text-amber-700"}`}>{value || "Price ID required"}</dd></div>;
}
