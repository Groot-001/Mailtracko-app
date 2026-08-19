import { api } from "../../../shared/api/axios";
import type { OnboardingState } from "../types/onboarding.types";

export interface CreateOrganizationPayload {
  name: string;
  website_url?: string;
  org_size?: string;
  monthly_email_volume?: string;
  domain_email?: string;
  org_logo?: string;
  description?: string;
  industry_sector?: string;
  source?: string;
  theme: "light" | "dark";
  timezone?: string;
  onboarding_skipped: boolean;
}

export const uploadOnboardingLogo = async (file: File): Promise<string> => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<{ data: { url: string } }>(
    "/organizations/onboarding-logo",
    formData
  );
  return response.data.data.url;
};

export const createOrganization = async (finalData: OnboardingState) => {
  // Map the local wizard state to the final organization creation payload
  const payload: CreateOrganizationPayload = {
    name: finalData.organization.organizationName,
    website_url: finalData.organization.websiteUrl || undefined,
    org_size: finalData.organization.organizationSize || undefined,
    monthly_email_volume: finalData.monthlyEmailVolume || undefined,
    domain_email: finalData.organization.companyEmailDomain || undefined,
    org_logo: finalData.organization.logoUrl || undefined,
    description: finalData.organization.description || undefined,
    industry_sector: finalData.industrySector || undefined,
    source: finalData.source || undefined,
    theme: finalData.theme,
    timezone: "UTC",
    onboarding_skipped: finalData.isSkipped,
  };

  try {
    const response = await api.post("/organizations/", payload);
    return response.data;
  } catch (error) {
    console.error("Onboarding API error during creation:", error);
    throw error;
  }
};
