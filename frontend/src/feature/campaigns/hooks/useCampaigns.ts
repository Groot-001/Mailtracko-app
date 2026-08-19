import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as campaignApi from "../api/campaignApi";
import type {
  CampaignListParams,
  ConfigureABTestPayload,
  ConfigureSequencePayload,
  CreateCampaignPayload,
  UpdateCampaignPayload,
} from "../types/campaign.types";

export const campaignKeys = {
  all: ["campaigns"] as const,
  list: (params: CampaignListParams) => ["campaigns", "list", params] as const,
  summary: ["campaigns", "summary"] as const,
  detail: (uuid: string) => ["campaigns", "detail", uuid] as const,
  recipients: (uuid: string) => ["campaigns", uuid, "recipients"] as const,
  sequence: (uuid: string) => ["campaigns", uuid, "sequence"] as const,
  abTest: (uuid: string) => ["campaigns", uuid, "ab-test"] as const,
  analytics: (uuid: string) => ["campaigns", uuid, "analytics"] as const,
};

export const useCampaigns = (params: CampaignListParams) =>
  useQuery({
    queryKey: campaignKeys.list(params),
    queryFn: () => campaignApi.listCampaigns(params),
    refetchInterval: 15_000,
    refetchIntervalInBackground: false,
  });

export const useCampaignSummary = () =>
  useQuery({
    queryKey: campaignKeys.summary,
    queryFn: campaignApi.getCampaignSummary,
    refetchInterval: 15_000,
    refetchIntervalInBackground: false,
  });

export const useCampaign = (uuid: string) =>
  useQuery({ queryKey: campaignKeys.detail(uuid), queryFn: () => campaignApi.getCampaign(uuid), enabled: Boolean(uuid) });

export const useCampaignRecipients = (uuid: string) =>
  useQuery({ queryKey: campaignKeys.recipients(uuid), queryFn: () => campaignApi.listCampaignRecipients(uuid), enabled: Boolean(uuid) });

export const useSequence = (uuid: string, enabled = true) =>
  useQuery({ queryKey: campaignKeys.sequence(uuid), queryFn: () => campaignApi.getSequence(uuid), enabled: Boolean(uuid) && enabled });

export const useABTest = (uuid: string, enabled = true) =>
  useQuery({ queryKey: campaignKeys.abTest(uuid), queryFn: () => campaignApi.getABTest(uuid), enabled: Boolean(uuid) && enabled });

export const useCampaignAnalytics = (uuid: string) =>
  useQuery({
    queryKey: campaignKeys.analytics(uuid),
    queryFn: () => campaignApi.getCampaignAnalytics(uuid),
    enabled: Boolean(uuid),
  });

const useCampaignMutation = <TData, TVariables>(
  mutationFn: (variables: TVariables) => Promise<TData>,
) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: campaignKeys.all }),
  });
};

export const useCreateCampaign = () =>
  useCampaignMutation((payload: CreateCampaignPayload) => campaignApi.createCampaign(payload));
export const useUpdateCampaign = () =>
  useCampaignMutation(({ uuid, payload }: { uuid: string; payload: UpdateCampaignPayload }) =>
    campaignApi.updateCampaign(uuid, payload),
  );
export const useDuplicateCampaign = () => useCampaignMutation((uuid: string) => campaignApi.duplicateCampaign(uuid));
export const useConfigureSequence = () =>
  useCampaignMutation(({ uuid, payload }: { uuid: string; payload: ConfigureSequencePayload }) =>
    campaignApi.configureSequence(uuid, payload),
  );
export const usePreviewSequence = () =>
  useMutation({
    mutationFn: ({ uuid, startsAt }: { uuid: string; startsAt?: string | null }) =>
      campaignApi.previewSequence(uuid, startsAt),
  });

export const useConfigureABTest = () =>
  useCampaignMutation(({ uuid, payload }: { uuid: string; payload: ConfigureABTestPayload }) =>
    campaignApi.configureABTest(uuid, payload),
  );
export const useSelectABWinner = () =>
  useCampaignMutation(
    ({ uuid, variantType }: { uuid: string; variantType?: "a" | "b" }) =>
      campaignApi.selectABWinner(uuid, variantType),
  );
export const useReviewCampaign = () => useMutation({ mutationFn: campaignApi.reviewCampaign });
export const useScheduleCampaign = () =>
  useCampaignMutation(({ uuid, scheduledAt, timezone }: { uuid: string; scheduledAt: string; timezone: string }) =>
    campaignApi.scheduleCampaign(uuid, scheduledAt, timezone),
  );
export const useLaunchCampaign = () => useCampaignMutation((uuid: string) => campaignApi.launchCampaign(uuid));
export const usePauseCampaign = () => useCampaignMutation((uuid: string) => campaignApi.pauseCampaign(uuid));
export const useResumeCampaign = () => useCampaignMutation((uuid: string) => campaignApi.resumeCampaign(uuid));
export const useCancelCampaign = () => useCampaignMutation((uuid: string) => campaignApi.cancelCampaign(uuid));
export const useArchiveCampaign = () => useCampaignMutation((uuid: string) => campaignApi.archiveCampaign(uuid));
export const useRestoreCampaign = () => useCampaignMutation((uuid: string) => campaignApi.restoreCampaign(uuid));
export const useDeleteCampaign = () => useCampaignMutation((uuid: string) => campaignApi.deleteCampaign(uuid));
