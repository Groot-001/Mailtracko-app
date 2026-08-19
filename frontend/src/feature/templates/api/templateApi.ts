import { api } from "../../../shared/api/axios";
import type { ApiSuccessResponse } from "../../../shared/types/api.types";
import type {
  EmailTemplate,
  EmailTemplateDetail,
  CreateTemplateCategoryPayload,
  TemplateAsset,
  TemplateCategory,
  TemplateDashboardSummary,
  TemplateListParams,
  TemplateListResult,
  TemplatePayload,
  TemplatePreviewPayload,
  TemplatePreviewResult,
  TestEmailPayload,
} from "../types/template.types";

const cleanParams = (params?: TemplateListParams) => ({
  status: params?.status || undefined,
  include_archived: params?.include_archived ?? false,
  category_id: params?.category_id,
  search: params?.search?.trim() || undefined,
  limit: params?.limit ?? 10,
  offset: params?.offset ?? 0,
});

export const listTemplates = async (
  params?: TemplateListParams,
): Promise<TemplateListResult> => {
  const { data } = await api.get<ApiSuccessResponse<TemplateListResult>>("/templates/", {
    params: cleanParams(params),
  });
  return data.data;
};

export const getTemplateDashboardSummary = async (): Promise<TemplateDashboardSummary> => {
  const { data } = await api.get<ApiSuccessResponse<TemplateDashboardSummary>>(
    "/templates/dashboard-summary",
  );
  return data.data;
};

export const getTemplate = async (templateUuid: string): Promise<EmailTemplateDetail> => {
  const { data } = await api.get<
    ApiSuccessResponse<{ template: EmailTemplateDetail }>
  >(`/templates/${templateUuid}`);
  return data.data.template;
};

export const createTemplate = async (payload: TemplatePayload): Promise<EmailTemplate> => {
  const { data } = await api.post<ApiSuccessResponse<{ template: EmailTemplate }>>(
    "/templates/",
    payload,
  );
  return data.data.template;
};

export const updateTemplate = async (
  templateUuid: string,
  payload: Partial<TemplatePayload>,
): Promise<EmailTemplate> => {
  const { data } = await api.patch<ApiSuccessResponse<{ template: EmailTemplate }>>(
    `/templates/${templateUuid}`,
    payload,
  );
  return data.data.template;
};

export const publishTemplate = async (templateUuid: string): Promise<EmailTemplate> => {
  const { data } = await api.post<ApiSuccessResponse<{ template: EmailTemplate }>>(
    `/templates/${templateUuid}/publish`,
  );
  return data.data.template;
};

export interface TemplateCampaignUsage {
  in_use: boolean;
  usage_count: number;
}

export const getTemplateCampaignUsage = async (templateUuid: string): Promise<TemplateCampaignUsage> => {
  const { data } = await api.get<ApiSuccessResponse<TemplateCampaignUsage>>(
    `/templates/${templateUuid}/campaign-usage`,
  );
  return data.data;
};

export const archiveTemplate = async (templateUuid: string): Promise<EmailTemplate> => {
  const { data } = await api.post<ApiSuccessResponse<{ template: EmailTemplate }>>(
    `/templates/${templateUuid}/archive`,
  );
  return data.data.template;
};

export const restoreTemplate = async (templateUuid: string): Promise<EmailTemplate> => {
  const { data } = await api.post<ApiSuccessResponse<{ template: EmailTemplate }>>(
    `/templates/${templateUuid}/restore`,
  );
  return data.data.template;
};

export const duplicateTemplate = async (
  templateUuid: string,
  name?: string,
): Promise<EmailTemplate> => {
  const { data } = await api.post<ApiSuccessResponse<{ template: EmailTemplate }>>(
    `/templates/${templateUuid}/duplicate`,
    name ? { name } : {},
  );
  return data.data.template;
};

export const deleteTemplate = async (templateUuid: string): Promise<void> => {
  await api.delete(`/templates/${templateUuid}`);
};

export const previewTemplate = async (
  payload: TemplatePreviewPayload,
): Promise<TemplatePreviewResult> => {
  const { data } = await api.post<ApiSuccessResponse<TemplatePreviewResult>>(
    "/email_templates/preview",
    payload,
  );
  return data.data;
};

export const sendTemplateTestEmail = async (payload: TestEmailPayload): Promise<void> => {
  await api.post("/email_templates/test-email", payload);
};

export const listTemplateCategories = async (): Promise<TemplateCategory[]> => {
  const { data } = await api.get<
    ApiSuccessResponse<{ items: TemplateCategory[] }>
  >("/templates/categories");
  return data.data.items;
};

export const listSystemTemplateCategories = async (): Promise<TemplateCategory[]> => {
  const { data } = await api.get<
    ApiSuccessResponse<{ items: TemplateCategory[] }>
  >("/template-gallery/categories");
  return data.data.items;
};

export const createTemplateCategory = async (
  payload: CreateTemplateCategoryPayload,
): Promise<TemplateCategory> => {
  const { data } = await api.post<ApiSuccessResponse<TemplateCategory>>(
    "/templates/categories",
    payload,
  );
  return data.data;
};

export const listSystemTemplates = async (
  params?: Omit<TemplateListParams, "status">,
): Promise<TemplateListResult> => {
  const { data } = await api.get<ApiSuccessResponse<TemplateListResult>>(
    "/template-gallery/templates",
    {
      params: {
        category_id: params?.category_id,
        search: params?.search?.trim() || undefined,
        limit: params?.limit ?? 20,
        offset: params?.offset ?? 0,
      },
    },
  );
  return data.data;
};

export const copySystemTemplate = async (templateUuid: string): Promise<EmailTemplate> => {
  const { data } = await api.post<ApiSuccessResponse<{ template: EmailTemplate }>>(
    `/template-gallery/templates/${templateUuid}/copy`,
  );
  return data.data.template;
};

export const uploadTemplateImage = async (templateUuid: string, file: File): Promise<TemplateAsset> => {
  const form = new FormData();
  form.append("usage", "inline");
  form.append("file", file);
  const { data } = await api.post<ApiSuccessResponse<{ asset: TemplateAsset }>>(
    `/templates/${templateUuid}/assets`,
    form,
  );
  return data.data.asset;
};
