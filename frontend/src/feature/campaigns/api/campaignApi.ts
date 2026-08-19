import axios from "axios";
import { api } from "../../../shared/api/axios";
import type { ApiSuccessResponse } from "../../../shared/types/api.types";
import type {
  ABTestResponse,
  Campaign,
  CampaignAnalytics,
  CampaignListParams,
  CampaignListResult,
  CampaignRecipientListResult,
  CampaignReview,
  CampaignSummary,
  ConfigureABTestPayload,
  ConfigureSequencePayload,
  CreateCampaignPayload,
  SequencePreview,
  SequenceResponse,
  UpdateCampaignPayload,
} from "../types/campaign.types";

export const listCampaigns = async (params: CampaignListParams): Promise<CampaignListResult> => {
  const { data } = await api.get<ApiSuccessResponse<CampaignListResult>>("/campaigns", {
    params: {
      search: params.search?.trim() || undefined,
      status: params.status || undefined,
      campaign_type: params.campaign_type || undefined,
      email_account_uuid: params.email_account_uuid || undefined,
      include_archived: params.include_archived ?? false,
      limit: params.limit ?? 10,
      offset: params.offset ?? 0,
    },
  });
  return data.data;
};

export const getCampaignSummary = async (): Promise<CampaignSummary> => {
  const { data } = await api.get<ApiSuccessResponse<CampaignSummary>>("/campaigns/summary");
  return data.data;
};

export const createCampaign = async (payload: CreateCampaignPayload): Promise<Campaign> => {
  const { data } = await api.post<ApiSuccessResponse<Campaign>>("/campaigns", payload);
  return data.data;
};

export const getCampaign = async (uuid: string): Promise<Campaign> => {
  const { data } = await api.get<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}`);
  return data.data;
};

export const updateCampaign = async (uuid: string, payload: UpdateCampaignPayload): Promise<Campaign> => {
  const { data } = await api.patch<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}`, payload);
  return data.data;
};

export const duplicateCampaign = async (uuid: string): Promise<Campaign> => {
  const { data } = await api.post<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}/duplicate`);
  return data.data;
};

export const configureSequence = async (
  uuid: string,
  payload: ConfigureSequencePayload,
): Promise<SequenceResponse> => {
  const { data } = await api.put<ApiSuccessResponse<SequenceResponse>>(`/campaigns/${uuid}/sequence`, payload);
  return data.data;
};

export const getSequence = async (uuid: string): Promise<SequenceResponse | null> => {
  try {
    const { data } = await api.get<ApiSuccessResponse<SequenceResponse>>(`/campaigns/${uuid}/sequence`);
    return data.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) return null;
    throw error;
  }
};


export const previewSequence = async (
  uuid: string,
  startsAt?: string | null,
): Promise<SequencePreview> => {
  const { data } = await api.post<ApiSuccessResponse<SequencePreview>>(
    `/campaigns/${uuid}/sequence/preview`,
    { starts_at: startsAt ?? null },
  );
  return data.data;
};
export const configureABTest = async (
  uuid: string,
  payload: ConfigureABTestPayload,
): Promise<ABTestResponse> => {
  const { data } = await api.put<ApiSuccessResponse<ABTestResponse>>(`/campaigns/${uuid}/ab-test`, payload);
  return data.data;
};

export const getABTest = async (uuid: string): Promise<ABTestResponse | null> => {
  try {
    const { data } = await api.get<ApiSuccessResponse<ABTestResponse>>(`/campaigns/${uuid}/ab-test`);
    return data.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) return null;
    throw error;
  }
};

export const selectABWinner = async (
  uuid: string,
  variantType?: "a" | "b",
): Promise<ABTestResponse> => {
  const { data } = await api.post<ApiSuccessResponse<ABTestResponse>>(
    `/campaigns/${uuid}/ab-test/winner`,
    { variant_type: variantType ?? null },
  );
  return data.data;
};

export const reviewCampaign = async (uuid: string): Promise<CampaignReview> => {
  const { data } = await api.post<ApiSuccessResponse<CampaignReview>>(`/campaigns/${uuid}/review`);
  return data.data;
};

export const scheduleCampaign = async (
  uuid: string,
  scheduledAt: string,
  timezone: string,
): Promise<Campaign> => {
  const { data } = await api.post<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}/schedule`, {
    scheduled_at: scheduledAt,
    timezone,
  });
  return data.data;
};

export const launchCampaign = async (uuid: string): Promise<Campaign> => {
  const { data } = await api.post<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}/launch`);
  return data.data;
};

export const pauseCampaign = async (uuid: string): Promise<Campaign> => {
  const { data } = await api.post<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}/pause`);
  return data.data;
};

export const resumeCampaign = async (uuid: string): Promise<Campaign> => {
  const { data } = await api.post<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}/resume`);
  return data.data;
};

export const cancelCampaign = async (uuid: string): Promise<Campaign> => {
  const { data } = await api.post<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}/cancel`);
  return data.data;
};

export const archiveCampaign = async (uuid: string): Promise<Campaign> => {
  const { data } = await api.post<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}/archive`);
  return data.data;
};

export const restoreCampaign = async (uuid: string): Promise<Campaign> => {
  const { data } = await api.post<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}/restore`);
  return data.data;
};

export const deleteCampaign = async (uuid: string): Promise<Campaign> => {
  const { data } = await api.delete<ApiSuccessResponse<Campaign>>(`/campaigns/${uuid}`);
  return data.data;
};

export const getCampaignAnalytics = async (uuid: string): Promise<CampaignAnalytics> => {
  const { data } = await api.get<ApiSuccessResponse<CampaignAnalytics>>(
    `/campaigns/${uuid}/analytics`,
  );
  return data.data;
};

export const listCampaignRecipients = async (
  uuid: string,
  limit = 50,
  offset = 0,
): Promise<CampaignRecipientListResult> => {
  const { data } = await api.get<ApiSuccessResponse<CampaignRecipientListResult>>(
    `/campaigns/${uuid}/recipients`,
    { params: { limit, offset } },
  );
  return data.data;
};
