import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listInvitations,
  inviteMember,
  resendInvitation,
  revokeInvitation,
  type ListInvitationsParams,
} from "../api/organizationApi";
import type { InviteMemberPayload } from "../types/organization.types";

export const INVITATIONS_QUERY_KEY = ["organization", "invitations"] as const;

export const useInvitations = (params?: ListInvitationsParams) => {
  return useQuery({
    queryKey: [...INVITATIONS_QUERY_KEY, params],
    queryFn: () => listInvitations(params),
    staleTime: 1000 * 30,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });
};

export const usePendingInvitations = () => {
  return useInvitations({ status: "pending", limit: 50 });
};

export const useInviteMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: InviteMemberPayload) => inviteMember(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: INVITATIONS_QUERY_KEY });
    },
  });
};

export const useResendInvitation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invitationUuid: string) => resendInvitation(invitationUuid),
    onSuccess: (updated) => {
      queryClient.setQueriesData(
        { queryKey: INVITATIONS_QUERY_KEY },
        (existing: unknown) => {
          if (!existing || typeof existing !== "object" || !("items" in existing)) return existing;
          const list = existing as { items: Array<{ uuid: string }>; [key: string]: unknown };
          return {
            ...list,
            items: list.items.map((item) => item.uuid === updated.uuid ? updated : item),
          };
        },
      );
      queryClient.invalidateQueries({ queryKey: INVITATIONS_QUERY_KEY });
    },
  });
};

export const useRevokeInvitation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invitationUuid: string) => revokeInvitation(invitationUuid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: INVITATIONS_QUERY_KEY });
    },
  });
};
