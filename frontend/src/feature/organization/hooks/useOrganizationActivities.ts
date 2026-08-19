import { useQuery } from "@tanstack/react-query";
import { listRecentActivities, type ListActivitiesParams } from "../api/organizationApi";

export const ACTIVITIES_QUERY_KEY = ["organization", "activities"] as const;

export const useOrganizationActivities = (params?: ListActivitiesParams) => {
  return useQuery({
    queryKey: [...ACTIVITIES_QUERY_KEY, params],
    queryFn: () => listRecentActivities(params),
    staleTime: 1000 * 60, // 1 min
  });
};
