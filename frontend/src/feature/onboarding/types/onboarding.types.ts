export type IndustrySectorOption =
  | "technology"
  | "finance"
  | "healthcare"
  | "education"
  | "ecommerce"
  | "real_estate"
  | "consulting"
  | "manufacturing"
  | "others";

export type SourceDiscoveryOption =
  | "referral"
  | "linkedin"
  | "youtube"
  | "marketplace"
  | "newsletter"
  | "events_webinar"
  | "social_media"
  | "others";

export type ThemeOption = "light" | "dark";

export interface OrganizationData {
  organizationName: string;
  websiteUrl: string;
  organizationSize: string;
  companyEmailDomain: string;
  logoUrl?: string;
  description?: string;
}

export interface OnboardingState {
  currentStep: number;
  organization: OrganizationData;
  monthlyEmailVolume: string;
  industrySector: IndustrySectorOption | string;
  source: SourceDiscoveryOption | string;
  theme: ThemeOption;
  isCompleted: boolean;
  isSkipped: boolean;
}

export interface StepMeta {
  id: number;
  label: string;
  shortDescription: string;
}
