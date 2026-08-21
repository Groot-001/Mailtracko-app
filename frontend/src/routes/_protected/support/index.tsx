import { useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { BookOpen, ExternalLink, LifeBuoy, Loader2, MessageCircle, Search, Send } from "lucide-react";
import { AppSelect } from "../../../shared/components/AppSelect";

import {
  createSupportTicket,
  getPlatformAccess,
  getSupportArticles,
  getSupportTickets,
} from "../../../feature/platform/api/platformApi";

export const Route = createFileRoute("/_protected/support/")({ component: SupportCenter });

const supportTicketSchema = z.object({
  subject: z
    .string()
    .trim()
    .min(3, "Subject must contain at least 3 characters.")
    .max(100, "Subject cannot exceed 100 characters."),
  description: z
    .string()
    .trim()
    .min(10, "Description must contain at least 10 characters.")
    .max(2000, "Description cannot exceed 2000 characters."),
  category: z.enum(["general", "campaign", "deliverability", "billing", "security"]),
  priority: z.enum(["low", "normal", "high", "urgent"]),
});

type SupportTicketValues = z.infer<typeof supportTicketSchema>;

function SupportCenter() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<SupportTicketValues>({
    resolver: zodResolver(supportTicketSchema),
    defaultValues: {
      subject: "",
      description: "",
      category: "general",
      priority: "normal",
    },
  });

  const access = useQuery({ queryKey: ["platform", "access"], queryFn: getPlatformAccess });
  const articles = useQuery({ queryKey: ["support", "articles", search], queryFn: () => getSupportArticles(search) });
  const tickets = useQuery({ queryKey: ["support", "tickets"], queryFn: getSupportTickets });

  const create = useMutation({
    mutationFn: createSupportTicket,
    onSuccess: () => {
      reset();
      queryClient.invalidateQueries({ queryKey: ["support", "tickets"] });
    },
  });

  const onSubmit = (data: SupportTicketValues) => {
    create.mutate(data);
  };

  return (
    <div className="mt-page-container space-y-6">
      <header className="mt-support-hero rounded-3xl border border-[#E6DDBF] bg-gradient-to-br from-[#FFF8DF] to-white p-7">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
          <div className="flex items-start gap-4">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-[#8F740D] text-white">
              <LifeBuoy className="h-6 w-6" />
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#8F740D]">Customer support</p>
              <h1 className="mt-1 text-2xl font-bold text-[#1A1C1C]">How can we help?</h1>
              <p className="mt-1 text-sm text-[#756F60]">
                Search the live knowledge base or open a tenant-scoped support ticket.
              </p>
              {access.data?.support_email && (
                <a
                  className="mt-3 inline-block text-xs font-semibold text-[#6A5B00] underline"
                  href={`mailto:${access.data.support_email}`}
                >
                  {access.data.support_email}
                </a>
              )}
            </div>
          </div>
          {access.data?.chatboq_widget_url && (
            <a
              href={access.data.chatboq_widget_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-[#1A1C1C] px-4 py-2.5 text-xs font-bold text-white"
            >
              <MessageCircle className="h-4 w-4" /> Start live chat <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <section className="rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-[#8F740D]" />
              <h2 className="font-bold">Knowledge base</h2>
            </div>
            <label className="relative mt-4 block">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9A9487]" />
              <span className="sr-only">Search support articles</span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search setup, campaigns, billing, security…"
                className="w-full rounded-xl border border-[#CEC6B0]/60 py-3 pl-10 pr-3 text-sm"
              />
            </label>
            <div className="mt-5 divide-y divide-[#F4F1E8]">
              {articles.isLoading ? (
                <Loader2 className="my-8 h-5 w-5 animate-spin" />
              ) : (
                articles.data?.items.map((article) => (
                  <article key={article.uuid} className="py-4">
                    <p className="text-[10px] font-bold uppercase text-[#8F740D]">{article.category}</p>
                    <h3 className="mt-1 text-sm font-bold">{article.title}</h3>
                    {article.summary && <p className="mt-1 text-xs leading-relaxed text-[#756F60]">{article.summary}</p>}
                  </article>
                ))
              )}
              {!articles.isLoading && !articles.data?.items.length && (
                <p className="py-8 text-center text-sm text-[#756F60]">No published articles match your search.</p>
              )}
            </div>
          </section>

          <section className="overflow-hidden rounded-2xl border border-[#CEC6B0]/50 bg-white">
            <div className="border-b border-[#EEE9DC] p-5">
              <h2 className="font-bold">Your tickets</h2>
              <p className="text-xs text-[#756F60]">Visible to members of this workspace.</p>
            </div>
            <div className="divide-y divide-[#F4F1E8]">
              {tickets.isLoading ? (
                <Loader2 className="m-6 h-5 w-5 animate-spin" />
              ) : (
                tickets.data?.items.map((ticket) => (
                  <article key={ticket.uuid} className="flex items-start justify-between gap-4 p-5">
                    <div>
                      <p className="text-sm font-semibold">{ticket.subject}</p>
                      <p className="mt-1 text-xs text-[#756F60]">
                        {ticket.category} ·{" "}
                        {new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(
                          new Date(ticket.created_at),
                        )}
                      </p>
                    </div>
                    <span className="rounded-full bg-[#F7F4E8] px-2.5 py-1 text-[10px] font-bold uppercase text-[#6A5B00]">
                      {ticket.status.replaceAll("_", " ")}
                    </span>
                  </article>
                ))
              )}
              {!tickets.isLoading && !tickets.data?.items.length && (
                <p className="p-8 text-center text-sm text-[#756F60]">No support tickets in this workspace.</p>
              )}
            </div>
          </section>
        </div>

        <aside className="h-fit rounded-2xl border border-[#CEC6B0]/50 bg-white p-6">
          <div className="flex items-center gap-2">
            <Send className="h-5 w-5 text-[#8F740D]" />
            <h2 className="font-bold">Open a ticket</h2>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-[#756F60]">
            Include what you expected, what happened, and any relevant campaign or account identifier.
          </p>
          <form onSubmit={handleSubmit(onSubmit)} className="mt-5 space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="support-subject" className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                Subject
              </label>
              <input
                id="support-subject"
                type="text"
                {...register("subject")}
                className="w-full rounded-xl border border-[#CEC6B0]/60 px-3 py-2.5 text-sm focus:outline-none focus:border-[#8F740D] bg-white text-[#1A1C1C]"
              />
              {errors.subject && <p role="alert" className="text-xs font-medium text-red-600 mt-1">{errors.subject.message}</p>}
            </div>

            <div className="space-y-1.5">
              <label htmlFor="support-description" className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                Description
              </label>
              <textarea
                id="support-description"
                rows={6}
                {...register("description")}
                className="w-full resize-y rounded-xl border border-[#CEC6B0]/60 px-3 py-2.5 text-sm focus:outline-none focus:border-[#8F740D] bg-white text-[#1A1C1C]"
              />
              {errors.description && (
                <p role="alert" className="text-xs font-medium text-red-600 mt-1">
                  {errors.description.message}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                  Category
                </label>
                <Controller
                  name="category"
                  control={control}
                  render={({ field }) => (
                    <AppSelect
                      value={field.value}
                      onValueChange={field.onChange}
                      ariaLabel="Support category"
                      options={[
                        { value: "general", label: "General" },
                        { value: "campaign", label: "Campaign" },
                        { value: "deliverability", label: "Deliverability" },
                        { value: "billing", label: "Billing" },
                        { value: "security", label: "Security" },
                      ]}
                    />
                  )}
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-[#4C4736] tracking-wide uppercase">
                  Priority
                </label>
                <Controller
                  name="priority"
                  control={control}
                  render={({ field }) => (
                    <AppSelect
                      value={field.value}
                      onValueChange={field.onChange}
                      ariaLabel="Support priority"
                      options={[
                        { value: "low", label: "Low" },
                        { value: "normal", label: "Normal" },
                        { value: "high", label: "High" },
                        { value: "urgent", label: "Urgent" },
                      ]}
                    />
                  )}
                />
              </div>
            </div>

            {create.isError && <p className="rounded-lg bg-red-50 p-3 text-xs text-red-800">The ticket could not be submitted.</p>}
            <button
              disabled={create.isPending}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#8F740D] hover:bg-[#725D0A] px-4 py-2.5 text-sm font-bold text-white transition-all disabled:opacity-50 cursor-pointer"
            >
              {create.isPending && <Loader2 className="h-4 w-4 animate-spin" />} Submit ticket
            </button>
          </form>
        </aside>
      </div>
    </div>
  );
}
