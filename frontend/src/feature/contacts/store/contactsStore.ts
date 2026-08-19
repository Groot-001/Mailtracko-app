import { create } from "zustand";
import type { ImportSuccessData } from "../types/contacts.types";

interface ContactsStoreState {
  selectedListUuid: string | null;
  search: string;
  subscribedFilter: boolean | undefined;
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
  importReportData: ImportSuccessData | null; // For sharing CSV import results with the report page

  setSelectedListUuid: (uuid: string | null) => void;
  setSearch: (search: string) => void;
  setSubscribedFilter: (sub: boolean | undefined) => void;
  setSort: (by: string, order: "asc" | "desc") => void;
  setPage: (page: number) => void;
  setImportReportData: (data: ImportSuccessData | null) => void;
  resetFilters: () => void;
}

export const useContactsStore = create<ContactsStoreState>((set) => ({
  selectedListUuid: null,
  search: "",
  subscribedFilter: undefined,
  sortBy: "created_at",
  sortOrder: "desc",
  page: 1,
  importReportData: null,

  setSelectedListUuid: (uuid) => set({ selectedListUuid: uuid }),
  setSearch: (search) => set({ search }),
  setSubscribedFilter: (sub) => set({ subscribedFilter: sub }),
  setSort: (by, order) => set({ sortBy: by, sortOrder: order }),
  setPage: (page) => set({ page }),
  setImportReportData: (data) => set({ importReportData: data }),
  resetFilters: () =>
    set({
      search: "",
      subscribedFilter: undefined,
      sortBy: "created_at",
      sortOrder: "desc",
      page: 1,
    }),
}));
