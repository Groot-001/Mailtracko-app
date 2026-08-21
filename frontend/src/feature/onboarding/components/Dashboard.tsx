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
import { PageContainer, PageSection } from "../../../shared/components/layout";

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
    title: "Prepare content",
    description: "Write reusable email drafts with variables for personalized outreach.",
    to: "/templates",
    action: "Design template",
    icon: FileText,
  },
  {
    step: "03",
    title: "Verify your email",
    description: "Connect your domain or external SMTP server to verify senders.",
    to: "/organization/settings",
    action: "Configure senders",
    icon: Mail,
  },
  {
    step: "04",
    title: "Launch outreach",
    description: "Choose a regular, sequence, or A/B campaign, then configure audience, sender, content, schedule, and review.",
    to: "/campaigns/new",
    action: "Create campaign",
    icon: Megaphone,
  },
] as const;

export const Dashboard = () => {
  return (
    <PageContainer>
      <PageSection className="!mt-0">
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
                Import recipients, create reusable content, connect a sender, and launch regular,
                sequence, or A/B campaigns from one workspace.
              </p>
              <div className="mt-8 flex flex-col gap-4 sm:flex-row">
                <Link
                  to="/campaigns/new"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#8F740D] px-5 py-3 text-sm font-bold text-white shadow-md hover:bg-[#735D0B]"
                >
                  <Send className="h-4 w-4" /> Launch campaign
                </Link>
                <Link
                  to="/contacts"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#D9D1BD] bg-white px-5 py-3 text-sm font-bold text-[#554716] hover:bg-[#FAF9F5]"
                >
                  Import recipients
                </Link>
              </div>
            </div>

            <div className="rounded-2xl bg-[#FCFAF5] p-6 border border-[#E8E1CE]/50">
              <h2 className="text-sm font-bold text-[#1A1C1C]">Setup check</h2>
              <p className="mt-1 text-xs text-[#746D5B]">Everything required is initialized.</p>
              <ul className="mt-5 space-y-4">
                {[
                  "PostgreSQL database connected",
                  "Redis messaging queuing ready",
                  "MailTracko core daemon active",
                  "System SMTP channels verified",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-2.5 text-xs text-[#4C4736]">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                    <span className="font-medium">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      </PageSection>

      <PageSection>
        <section>
          <div className="mb-4">
            <h2 className="text-xl font-bold text-[#1A1C1C]">Your campaign workflow</h2>
            <p className="mt-1 text-sm text-[#746D5B]">Complete these steps in order for the cleanest setup.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {workflow.map(({ step, title, description, to, action, icon: Icon }) => (
              <article
                key={step}
                className="flex min-h-[250px] flex-col rounded-2xl border border-[#E6DEC7] bg-white p-5 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#F5ECD2] text-[#806708]">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-xs font-bold tracking-widest text-[#B2A98F]">STEP {step}</span>
                </div>
                <h3 className="mt-5 text-base font-bold text-[#1A1C1C]">{title}</h3>
                <p className="mt-2 flex-1 text-sm leading-6 text-[#746D5B]">{description}</p>
                <Link
                  to={to}
                  className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#806708] hover:text-[#5F4D06]"
                >
                  {action} <ArrowRight className="h-4 w-4" />
                </Link>
              </article>
            ))}
          </div>
        </section>
      </PageSection>
    </PageContainer>
  );
};
