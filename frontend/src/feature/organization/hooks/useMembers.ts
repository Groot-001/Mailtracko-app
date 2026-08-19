import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listMembers,
  removeMember,
  updateMemberRole,
  updateMemberPermissions,
  type ListMembersParams,
} from "../api/organizationApi";

export const MEMBERS_QUERY_KEY = ["organization", "members"] as const;

export const useMembers = (params?: ListMembersParams) => {
  return useQuery({
    queryKey: [...MEMBERS_QUERY_KEY, params],
    queryFn: () => listMembers(params),
    placeholderData: (previous) => previous,
    staleTime: 1000 * 15,
    refetchInterval: 1000 * 30, // Presence/last-active refresh without F5.
    refetchIntervalInBackground: false,
  });
};

export const useUpdateMemberRole = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ memberUuid, roleCode }: { memberUuid: string; roleCode: "admin" | "member" }) =>
      updateMemberRole(memberUuid, roleCode),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: MEMBERS_QUERY_KEY }),
  });
};

export const useRemoveMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (memberId: number) => removeMember(memberId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MEMBERS_QUERY_KEY });
    },
  });
};
export const useUpdateMemberPermissions = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ memberUuid, permissions }: { memberUuid: string; permissions: Record<string, boolean> }) =>
      updateMemberPermissions(memberUuid, permissions),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MEMBERS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["platform", "access"] });
    },
  });
};

