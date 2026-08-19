import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  archiveTemplate,
  copySystemTemplate,
  createTemplate,
  createTemplateCategory,
  deleteTemplate,
  duplicateTemplate,
  getTemplate,
  getTemplateDashboardSummary,
  listSystemTemplates,
  listSystemTemplateCategories,
  listTemplateCategories,
  listTemplates,
  previewTemplate,
  publishTemplate,
  restoreTemplate,
  sendTemplateTestEmail,
  updateTemplate,
} from "../api/templateApi";
import type {
  CreateTemplateCategoryPayload,
  TemplateListParams,
  TemplatePayload,
  TemplatePreviewPayload,
  TestEmailPayload,
} from "../types/template.types";

export const templateKeys = {
  all: ["templates"] as const,
  list: (params: TemplateListParams) => ["templates", "list", params] as const,
  detail: (uuid: string) => ["templates", "detail", uuid] as const,
  summary: ["templates", "summary"] as const,
  categories: ["templates", "categories"] as const,
  systemCategories: ["templates", "system-categories"] as const,
  gallery: (params: Omit<TemplateListParams, "status">) =>
    ["templates", "gallery", params] as const,
};

export const useTemplates = (params: TemplateListParams) =>
  useQuery({
    queryKey: templateKeys.list(params),
    queryFn: () => listTemplates(params),
    placeholderData: keepPreviousData,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });

export const useTemplateSummary = () =>
  useQuery({
    queryKey: templateKeys.summary,
    queryFn: getTemplateDashboardSummary,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });

export const useTemplate = (uuid: string) =>
  useQuery({
    queryKey: templateKeys.detail(uuid),
    queryFn: () => getTemplate(uuid),
    enabled: Boolean(uuid),
  });

export const useTemplateCategories = () =>
  useQuery({
    queryKey: templateKeys.categories,
    queryFn: listTemplateCategories,
    staleTime: 1000 * 60 * 10,
  });

export const useSystemTemplateCategories = () =>
  useQuery({
    queryKey: templateKeys.systemCategories,
    queryFn: listSystemTemplateCategories,
    staleTime: 1000 * 60 * 10,
  });

export const useCreateTemplateCategory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateTemplateCategoryPayload) =>
      createTemplateCategory(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.categories });
      queryClient.invalidateQueries({ queryKey: templateKeys.summary });
    },
  });
};

export const useSystemTemplates = (params: Omit<TemplateListParams, "status">) =>
  useQuery({
    queryKey: templateKeys.gallery(params),
    queryFn: () => listSystemTemplates(params),
    placeholderData: keepPreviousData,
  });

const useTemplateMutation = <TData, TVariables>(
  mutationFn: (variables: TVariables) => Promise<TData>,
) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.all });
    },
  });
};

export const useCreateTemplate = () =>
  useTemplateMutation((payload: TemplatePayload) => createTemplate(payload));

export const useUpdateTemplate = () =>
  useTemplateMutation(
    ({ uuid, payload }: { uuid: string; payload: Partial<TemplatePayload> }) =>
      updateTemplate(uuid, payload),
  );

export const usePublishTemplate = () =>
  useTemplateMutation((uuid: string) => publishTemplate(uuid));

export const useArchiveTemplate = () =>
  useTemplateMutation((uuid: string) => archiveTemplate(uuid));

export const useRestoreTemplate = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (uuid: string) => restoreTemplate(uuid),
    onSuccess: (template) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.all });
      queryClient.invalidateQueries({ queryKey: templateKeys.detail(template.uuid) });
      queryClient.invalidateQueries({ queryKey: templateKeys.summary });
    },
  });
};

export const useDuplicateTemplate = () =>
  useTemplateMutation(({ uuid, name }: { uuid: string; name?: string }) =>
    duplicateTemplate(uuid, name),
  );

export const useDeleteTemplate = () =>
  useTemplateMutation((uuid: string) => deleteTemplate(uuid));

export const useCopySystemTemplate = () =>
  useTemplateMutation((uuid: string) => copySystemTemplate(uuid));

export const usePreviewTemplate = () =>
  useMutation({ mutationFn: (payload: TemplatePreviewPayload) => previewTemplate(payload) });

export const useSendTemplateTestEmail = () =>
  useMutation({ mutationFn: (payload: TestEmailPayload) => sendTemplateTestEmail(payload) });
