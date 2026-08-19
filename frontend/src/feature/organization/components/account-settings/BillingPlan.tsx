import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CalendarClock,
  Check,
  CreditCard,
  ExternalLink,
  Loader2,
  ReceiptText,
  RotateCcw,
  Sparkles,
} from "lucide-react";

import {
  cancelBillingSubscription,
  changeBillingPlan,
  createBillingCheckout,
  createBillingPortal,
  getBillingOverview,
  getPlatformAccess,
  resumeBillingSubscription,
} from "../../../platform/api/platformApi";
import { ConfirmDialog } from "../../../../shared/components/ConfirmDialog";

type BillingCycle = "monthly" | "annual";

const money = (cents: number, currency: string) =>
  new Intl.NumberFormat(undefined, { style: "currency", currency }).format(cents / 100);

const date = (value?: string | null) =>
  value ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(value)) : "—";

const errorMessage = (error: unknown) => {
  if (typeof error === "object" && error && "response" in error) {
    const response = (error as { response?: { data?: { message?: string } } }).response;
    return response?.data?.message || "The billing request could not be completed.";
  }
  return "The billing request could not be completed.";
};

export const BillingPlan = () => {
  const queryClient = useQueryClient();
  const [cycleOverride, setCycleOverride] = useState<BillingCycle | null>(null);
  const [promotionCode, setPromotionCode] = useState("");
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    const result = new URLSearchParams(window.location.search).get("checkout");
    if (result === "success") return "Checkout completed. Stripe is finalizing your subscription; billing status will refresh from the signed webhook.";
    if (result === "cancelled") return "Checkout was cancelled. No billing plan change was made.";
    return null;
  });
  const overview = useQuery({ queryKey: ["billing", "overview"], queryFn: getBillingOverview });
  const access = useQuery({ queryKey: ["platform", "access"], queryFn: getPlatformAccess });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["billing", "overview"] });
  const checkout = useMutation({
    mutationFn: createBillingCheckout,
    onSuccess: ({ url }) => window.location.assign(url),
  });
  const portal = useMutation({
    mutationFn: createBillingPortal,
    onSuccess: ({ url }) => window.location.assign(url),
  });
  const changePlan = useMutation({
    mutationFn: changeBillingPlan,
    onSuccess: async () => {
      await refresh();
      setNotice("Your Stripe subscription plan has been updated. Proration follows the platform billing policy.");
    },
  });
  const cancel = useMutation({
    mutationFn: cancelBillingSubscription,
    onSuccess: async () => {
      await refresh();
      setNotice("Cancellation is scheduled for the end of the current billing period.");
    },
  });
  const resume = useMutation({
    mutationFn: resumeBillingSubscription,
    onSuccess: async () => {
      await refresh();
      setNotice("Automatic renewal has been restored for this subscription.");
    },
  });

  if (overview.isLoading) {
    return (
      <div className="grid min-h-64 place-items-center text-[#8F740D]">
        <Loader2 className="h-6 w-6 animate-spin" aria-label="Loading billing information" />
      </div>
    );
  }

  if (overview.isError || !overview.data) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-800">
        Billing information is unavailable. Refresh the page or contact your platform administrator.
      </div>
    );
  }

  const data = overview.data;
  const current = data.subscription;
  const cycle = cycleOverride || current?.billing_cycle || "monthly";
  const pendingError = checkout.error || portal.error || changePlan.error || cancel.error || resume.error;
  const changing = checkout.isPending || changePlan.isPending;
  const canCancel = current?.provider_managed && access.data?.workspace_role === "owner";

  const selectPlan = (planCode: string) => {
    setNotice(null);
    if (current?.provider_managed) {
      changePlan.mutate({ plan_code: planCode, billing_cycle: cycle });
      return;
    }
    checkout.mutate({
      plan_code: planCode,
      billing_cycle: cycle,
      promotion_code: promotionCode.trim() || undefined,
    });
  };

  return (
    <div className="space-y-6">
      <ConfirmDialog
        open={cancelDialogOpen}
        onOpenChange={setCancelDialogOpen}
        title="Cancel subscription renewal?"
        description="Your subscription will remain active until the end of the current billing period, then automatic renewal will stop."
        confirmLabel="Cancel at period end"
        isLoading={cancel.isPending}
        onConfirm={() => {
          cancel.mutate(undefined, { onSuccess: () => setCancelDialogOpen(false) });
        }}
      />
      {!data.billing_enabled && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Online billing is disabled for this deployment. The current plan remains available, but Stripe actions require the server billing configuration.
        </div>
      )}

      {notice && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800" role="status">
          {notice}
        </div>
      )}

      {pendingError && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800" role="alert">
          {errorMessage(pendingError)}
        </div>
      )}

      <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-[#F1D442]/20 text-[#8F740D]">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#756F60]">Current plan</p>
                <h2 className="text-xl font-bold text-[#1A1C1C]">{current?.plan.name || "No active plan"}</h2>
              </div>
            </div>
            {current?.plan.description && <p className="max-w-xl text-sm text-[#4C4736]">{current.plan.description}</p>}
            <div className="flex flex-wrap gap-2">
              {current?.plan.features.map((feature) => (
                <span key={feature} className="inline-flex items-center gap-1.5 rounded-full bg-[#F7F4E8] px-3 py-1 text-xs font-medium text-[#594C05]">
                  <Check className="h-3.5 w-3.5" /> {feature}
                </span>
              ))}
            </div>
          </div>
          <div className="min-w-72 rounded-xl border border-[#CEC6B0]/50 bg-[#FBFAF6] p-4 text-sm">
            <dl className="space-y-3">
              <div className="flex justify-between gap-4"><dt className="text-[#756F60]">Status</dt><dd className="font-semibold capitalize">{current?.status || "inactive"}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-[#756F60]">Billing cycle</dt><dd className="font-semibold capitalize">{current?.billing_cycle || "—"}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-[#756F60]">Next renewal</dt><dd className="font-semibold">{date(current?.current_period_end)}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-[#756F60]">Seats</dt><dd className="font-semibold">{data.usage.team_members || 0} / {data.limits.team_members || "∞"}</dd></div>
            </dl>
            <button
              type="button"
              disabled={!data.billing_enabled || portal.isPending || !current?.provider_managed}
              onClick={() => portal.mutate()}
              className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#1A1C1C] px-4 py-2.5 text-xs font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {portal.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CreditCard className="h-4 w-4" />}
              Manage payment and invoices
            </button>
            {canCancel && (
              current.cancel_at_period_end ? (
                <button type="button" disabled={resume.isPending} onClick={() => resume.mutate()} className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-emerald-300 px-4 py-2.5 text-xs font-bold text-emerald-700 disabled:opacity-50">
                  {resume.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />} Resume renewal
                </button>
              ) : (
                <button type="button" disabled={cancel.isPending} onClick={() => setCancelDialogOpen(true)} className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-red-200 px-4 py-2.5 text-xs font-bold text-red-700 disabled:opacity-50">
                  {cancel.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CalendarClock className="h-4 w-4" />} Cancel at period end
                </button>
              )
            )}
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-base font-bold text-[#1A1C1C]">Available plans</h2>
            <p className="text-sm text-[#756F60]">Limits, prices, and provider availability come directly from the platform plan configuration.</p>
          </div>
          <div className="inline-flex rounded-xl border border-[#CEC6B0]/60 bg-white p-1">
            {(["monthly", "annual"] as BillingCycle[]).map((item) => (
              <button key={item} type="button" onClick={() => setCycleOverride(item)} className={`rounded-lg px-4 py-2 text-xs font-bold capitalize ${cycle === item ? "bg-[#1A1C1C] text-white" : "text-[#756F60]"}`}>
                {item}
              </button>
            ))}
          </div>
        </div>
        {!current?.provider_managed && data.billing_enabled && (
          <label className="block max-w-sm text-xs font-semibold text-[#4C4736]">
            Promotion code (optional)
            <input value={promotionCode} onChange={(event) => setPromotionCode(event.target.value)} maxLength={80} className="mt-1 w-full rounded-xl border border-[#CEC6B0]/70 px-3 py-2.5 text-sm font-normal uppercase outline-none focus:border-[#8F740D]" placeholder="Enter a valid code" />
          </label>
        )}
        <div className="grid gap-4 lg:grid-cols-3">
          {data.available_plans.map((plan) => {
            const selected = current?.plan.code === plan.code;
            const exactSelection = selected && current?.billing_cycle === cycle;
            const price = cycle === "annual" ? plan.annual_price_cents : plan.monthly_price_cents;
            const checkoutConfigured = cycle === "annual" ? plan.annual_checkout_configured : plan.monthly_checkout_configured;
            return (
              <article key={plan.uuid} className={`rounded-2xl border bg-white p-5 ${exactSelection ? "border-[#8F740D] ring-2 ring-[#F1D442]/40" : "border-[#CEC6B0]/50"}`}>
                <div className="flex items-start justify-between gap-3">
                  <div><h3 className="font-bold text-[#1A1C1C]">{plan.name}</h3><p className="mt-1 text-xs text-[#756F60]">{plan.description}</p></div>
                  {exactSelection && <span className="rounded-full bg-[#F1D442]/25 px-2 py-1 text-[10px] font-bold uppercase text-[#6A5B00]">Current</span>}
                </div>
                <p className="mt-5 text-2xl font-black text-[#1A1C1C]">{money(price, plan.currency)}<span className="text-xs font-medium text-[#756F60]"> / {cycle === "annual" ? "year" : "month"}</span></p>
                {cycle === "annual" && plan.annual_price_cents > 0 && <p className="mt-1 text-[11px] text-[#756F60]">Equivalent to {money(Math.round(plan.annual_price_cents / 12), plan.currency)} per month</p>}
                <ul className="mt-4 space-y-2 text-xs text-[#4C4736]">
                  {plan.features.slice(0, 6).map((feature) => <li key={feature} className="flex gap-2"><Check className="h-4 w-4 shrink-0 text-[#8F740D]" />{feature}</li>)}
                </ul>
                {!checkoutConfigured && data.billing_enabled && <p className="mt-4 rounded-lg bg-amber-50 p-2 text-[11px] text-amber-800">Stripe Price ID is not configured for this billing cycle.</p>}
                <button
                  type="button"
                  disabled={exactSelection || !data.billing_enabled || !checkoutConfigured || changing}
                  onClick={() => selectPlan(plan.code)}
                  className="mt-5 w-full rounded-xl border border-[#8F740D] px-4 py-2.5 text-xs font-bold text-[#6A5B00] hover:bg-[#F1D442]/10 disabled:cursor-not-allowed disabled:border-[#CEC6B0] disabled:text-[#9A9487]"
                >
                  {changing ? "Updating…" : exactSelection ? "Current plan" : current?.provider_managed ? "Change plan" : "Continue to Stripe"}
                </button>
              </article>
            );
          })}
        </div>
      </section>

      <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
        <div className="flex items-center gap-3"><ReceiptText className="h-5 w-5 text-[#8F740D]" /><div><h2 className="font-bold text-[#1A1C1C]">Invoice history</h2><p className="text-xs text-[#756F60]">Stripe-issued documents and webhook-synchronized payment status.</p></div></div>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead><tr className="border-b border-[#EEE9DC] text-[10px] uppercase tracking-wider text-[#756F60]"><th className="py-3">Invoice</th><th>Date</th><th>Description</th><th>Amount</th><th>Status</th><th className="text-right">Document</th></tr></thead>
            <tbody className="divide-y divide-[#F4F1E8]">
              {data.invoices.map((invoice) => (
                <tr key={invoice.uuid}><td className="py-3 font-semibold">{invoice.number || "Pending number"}</td><td>{date(invoice.paid_at || invoice.created_at)}</td><td>{invoice.description || "Subscription invoice"}</td><td>{money(invoice.amount_due_cents, invoice.currency)}</td><td className="capitalize">{invoice.status}</td><td className="text-right">{invoice.invoice_pdf_url || invoice.hosted_invoice_url ? <a href={invoice.invoice_pdf_url || invoice.hosted_invoice_url || "#"} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-semibold text-[#6A5B00]">Open <ExternalLink className="h-3.5 w-3.5" /></a> : "—"}</td></tr>
              ))}
            </tbody>
          </table>
          {!data.invoices.length && <p className="py-8 text-center text-sm text-[#756F60]">No invoices have been issued for this workspace.</p>}
        </div>
      </section>
    </div>
  );
};
