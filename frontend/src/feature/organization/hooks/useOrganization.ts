import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  editOrganization,
  getDeletionSummary,
  getOrganization,
  requestOrganizationDeletion,
} from "../api/organizationApi";
import type { EditOrganizationPayload } from "../types/organization.types";

export const ORGANIZATION_QUERY_KEY = ["organization"] as const;

export const useOrganization = () => {
  return useQuery({
    queryKey: ORGANIZATION_QUERY_KEY,
    queryFn: getOrganization,
    staleTime: 1000 * 60 * 5, // 5 min — org data rarely changes
  });
};

export const useEditOrganization = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      uuid,
      payload,
    }: {
      uuid: string;
      payload: EditOrganizationPayload;
    }) => editOrganization(uuid, payload),
    onSuccess: (updatedOrganization) => {
      // The PATCH response is the canonical updated organization. Put it in the
      // shared cache immediately so Settings, Overview, Account Actions and any
      // other useOrganization() consumer render the same saved values without a
      // manual refresh. Avoid invalidating the current organization query here:
      // an immediate refetch can race the mutation response and causes the form
      // and save button to visibly bounce between states.
      queryClient.setQueryData(ORGANIZATION_QUERY_KEY, updatedOrganization);

      // Related data can change as a side effect (for example the organization
      // updated audit activity), so refresh those independently in the background.
      void queryClient.invalidateQueries({ queryKey: ["organization", "activities"] });
      void queryClient.invalidateQueries({ queryKey: ["organization", "deletion-summary"] });
      void queryClient.invalidateQueries({ queryKey: ["platform", "access"] });
    },
  });
};

export const useRequestOrganizationDeletion = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: requestOrganizationDeletion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ORGANIZATION_QUERY_KEY });
    },
  });
};

export const useDeletionSummary = () => {
  return useQuery({
    queryKey: ["organization", "deletion-summary"],
    queryFn: getDeletionSummary,
    staleTime: 1000 * 30,
  });
};
