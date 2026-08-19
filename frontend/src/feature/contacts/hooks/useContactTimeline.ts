import { useQuery } from "@tanstack/react-query";
import { getContactTimeline } from "../api/contactsApi";

export const TIMELINE_KEY = ["contact-timeline"] as const;

export const useContactTimeline = (
  listUuid?: string,
  contactUuid?: string,
  limit = 50,
  offset = 0
) => {
  return useQuery({
    queryKey: [...TIMELINE_KEY, listUuid, contactUuid, limit, offset],
    queryFn: () => getContactTimeline(listUuid!, contactUuid!, limit, offset),
    enabled: !!listUuid && !!contactUuid,
    staleTime: 1000 * 60, // 1 minute
  });
};
