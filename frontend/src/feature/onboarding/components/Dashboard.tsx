import { Link } from "@tanstack/react-router";
import {
  ArrowRight,
  CheckCircle2,
  FileText,
  Mail,
  Megaphone,
  Send,
  Users,
} from "lucide-react";

const workflow = [
  {
    step: "01",
    title: "Import contacts",
    description: "Create a contact collection and upload a CSV or Excel file.",
    to: "/contacts",
    action: "Manage contacts",
    icon: Users,
  },
  {
    step: "02",
    title: "Create a template",
    description: "Write and preview the email content that your campaign will use.",
    to: "/templates/new",
    action: "Create template",
    icon: FileText,
  },
  {
    step: "03",
    title: "Connect a sender",
    description: "Connect Gmail or SMTP before sending campaign emails.",
    to: "/organization/account-settings/email-accounts",
    action: "Connect sender",
    icon: Send,
  },
  {
    step: "04",
    title: "Launch a campaign",
    description: "Choose a regular, sequence, or A/B campaign, then configure audience, sender, content, schedule, and review.",
    to: "/campaigns/new",
    action: "Create campaign",
    icon: Megaphone,
  },
] as const;

export const Dashboard = () => {
  return (
    <div className="mx-auto max-w-[1480px] space-y-8 px-4 py-6 sm:px-6 lg:px-8">
      <section className="overflow-hidden rounded-3xl border border-[#E6DEC7] bg-white shadow-sm">
        <div className="grid gap-8 px-6 py-8 lg:grid-cols-[1.35fr_.65fr] lg:px-10 lg:py-10">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#E8DFC5] bg-[#FFFBEE] px-3 py-1.5 text-xs font-semibold text-[#7A6208]">
              <CheckCircle2 className="h-4 w-4" /> Workspace ready
            </div>
            <h1 className="max-w-3xl text-3xl font-bold tracking-tight text-[#171711] sm:text-4xl">
              Run your complete email outreach workflow
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#6F6857]">
              Import recipients, create reusable content, connect a sender, and launch regular, sequence, or A/B campaigns from one workspace.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                to="/contacts"
                className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#725D0A]"
              >
                Start with contacts <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/campaigns"
                className="inline-flex items-center gap-2 rounded-xl border border-[#DCD3BC] bg-white px-4 py-2.5 text-sm font-semibold text-[#403919] hover:bg-[#FAF7EE]"
              >
                View campaigns
              </Link>
            </div>
          </div>
          <div className="flex items-center justify-center rounded-2xl bg-[#F8F1DD] p-8">
            <div className="flex h-28 w-28 items-center justify-center rounded-3xl bg-[#8F740D] shadow-lg shadow-[#8F740D]/20">
              <Mail className="h-14 w-14 text-white" />
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="mb-4">
          <h2 className="text-xl font-bold text-[#1A1C1C]">Your campaign workflow</h2>
          <p className="mt-1 text-sm text-[#746D5B]">Complete these steps in order for the cleanest setup.</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {workflow.map(({ step, title, description, to, action, icon: Icon }) => (
            <article key={step} className="flex min-h-[250px] flex-col rounded-2xl border border-[#E6DEC7] bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#F5ECD2] text-[#806708]">
                  <Icon className="h-5 w-5" />
                </div>
                <span className="text-xs font-bold tracking-widest text-[#B2A98F]">STEP {step}</span>
              </div>
              <h3 className="mt-5 text-base font-bold text-[#1A1C1C]">{title}</h3>
              <p className="mt-2 flex-1 text-sm leading-6 text-[#746D5B]">{description}</p>
              <Link to={to} className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#806708] hover:text-[#5F4D06]">
                {action} <ArrowRight className="h-4 w-4" />
              </Link>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
};
