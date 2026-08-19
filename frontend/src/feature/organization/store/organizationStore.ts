import { create } from "zustand";
import type { NotificationTab, RoleCode } from "../types/organization.types";

interface OrganizationStore {
  // Team Management
  memberSearchQuery: string;
  memberRoleFilter: RoleCode | "all";
  memberStatusFilter: string;
  invitePanelOpen: boolean;
  setMemberSearchQuery: (q: string) => void;
  setMemberRoleFilter: (role: RoleCode | "all") => void;
  setMemberStatusFilter: (status: string) => void;
  setInvitePanelOpen: (open: boolean) => void;

  // Roles & Permissions
  selectedRole: RoleCode;
  setSelectedRole: (role: RoleCode) => void;

  // Notifications
  notificationTab: NotificationTab;
  setNotificationTab: (tab: NotificationTab) => void;
}

export const useOrganizationStore = create<OrganizationStore>((set) => ({
  // Team Management
  memberSearchQuery: "",
  memberRoleFilter: "all",
  memberStatusFilter: "all",
  invitePanelOpen: false,
  setMemberSearchQuery: (q) => set({ memberSearchQuery: q }),
  setMemberRoleFilter: (role) => set({ memberRoleFilter: role }),
  setMemberStatusFilter: (status) => set({ memberStatusFilter: status }),
  setInvitePanelOpen: (open) => set({ invitePanelOpen: open }),

  // Roles & Permissions
  selectedRole: "owner",
  setSelectedRole: (role) => set({ selectedRole: role }),

  // Notifications
  notificationTab: "system",
  setNotificationTab: (tab) => set({ notificationTab: tab }),
}));
