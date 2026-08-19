import { api } from "../../../shared/api/axios";
import type {
  ApiSuccessResponse,
  EditOrganizationPayload,
  InvitationList,
  InviteMemberPayload,
  MemberList,
  Organization,
  OrganizationActivity,
  OrganizationDeletionSummary,
  OrganizationInvitation,
  OrganizationMember,
  PaginatedList,
} from "../types/organization.types";

// ─── Organization ─────────────────────────────────────────────────────────────

export const getOrganization = async (): Promise<Organization> => {
  const { data } = await api.get<
    ApiSuccessResponse<{ organization: Organization }>
  >("/organizations/current");
  return data.data.organization;
};

export const editOrganization = async (
  organizationUuid: string,
  payload: EditOrganizationPayload,
): Promise<Organization> => {
  const { data } = await api.patch<
    ApiSuccessResponse<{ current_organization: Organization }>
  >(`/organizations/${organizationUuid}`, payload);
  return data.data.current_organization;
};

export const uploadOrganizationLogo = async (
  file: File,
): Promise<{ url: string }> => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<
    ApiSuccessResponse<{ url: string }>
  >("/organizations/logo", formData);
  return data.data;
};

export const requestOrganizationDeletion = async (): Promise<void> => {
  await api.post("/organizations/delete-request");
};

// organizationApi.ts — add
export const getDeletionSummary =
  async (): Promise<OrganizationDeletionSummary> => {
    const { data } = await api.get<
      ApiSuccessResponse<OrganizationDeletionSummary>
    >("/organizations/deletion-summary");
    return data.data;
  };

// ─── Members ──────────────────────────────────────────────────────────────────

export interface ListMembersParams {
  status?: string;
  role?: "owner" | "admin" | "member";
  search?: string;
  limit?: number;
  offset?: number;
}

export const listMembers = async (
  params?: ListMembersParams,
): Promise<MemberList> => {
  const { data } = await api.get<ApiSuccessResponse<MemberList>>(
    "/organizations/members",
    {
      params: {
        status: params?.status,
        role: params?.role,
        search: params?.search,
        limit: params?.limit ?? 50,
        offset: params?.offset ?? 0,
      },
    },
  );
  return data.data;
};

export const removeMember = async (memberId: number): Promise<void> => {
  await api.delete(`/organizations/members/${memberId}`);
};

export const updateMemberRole = async (
  memberUuid: string,
  roleCode: "admin" | "member",
): Promise<{ uuid: string; role_code: string }> => {
  const { data } = await api.patch<
    ApiSuccessResponse<{ uuid: string; role_code: string }>
  >(`/platform/workspace/members/${memberUuid}/role`, { role_code: roleCode });
  return data.data;
};

export const updateMemberPermissions = async (
  memberUuid: string,
  permissions: Record<string, boolean>,
): Promise<{ uuid: string; role_code: string; permissions: Record<string, boolean>; effective_permissions: Record<string, boolean> }> => {
  const { data } = await api.patch<
    ApiSuccessResponse<{ uuid: string; role_code: string; permissions: Record<string, boolean>; effective_permissions: Record<string, boolean> }>
  >(`/platform/workspace/members/${memberUuid}/permissions`, { permissions });
  return data.data;
};

// ─── Invitations ──────────────────────────────────────────────────────────────

export interface ListInvitationsParams {
  status?: string;
  limit?: number;
  offset?: number;
}

export const listInvitations = async (
  params?: ListInvitationsParams,
): Promise<InvitationList> => {
  const { data } = await api.get<ApiSuccessResponse<InvitationList>>(
    "/organizations/invitations",
    {
      params: {
        status: params?.status,
        limit: params?.limit ?? 50,
        offset: params?.offset ?? 0,
      },
    },
  );
  return data.data;
};

export const inviteMember = async (
  payload: InviteMemberPayload,
): Promise<OrganizationInvitation> => {
  const { data } = await api.post<ApiSuccessResponse<OrganizationInvitation>>(
    "/organizations/invitations",
    payload,
  );
  return data.data;
};

export const resendInvitation = async (
  invitationUuid: string,
): Promise<OrganizationInvitation> => {
  const { data } = await api.post<ApiSuccessResponse<OrganizationInvitation>>(
    `/organizations/invitations/${invitationUuid}/resend`,
  );
  return data.data;
};

export const revokeInvitation = async (
  invitationUuid: string,
): Promise<void> => {
  await api.post(`/organizations/invitations/${invitationUuid}/revoke`);
};

// ─── Activities ───────────────────────────────────────────────────────────────

export interface ListActivitiesParams {
  limit?: number;
  offset?: number;
}

export const listRecentActivities = async (
  params?: ListActivitiesParams,
): Promise<PaginatedList<OrganizationActivity>> => {
  const { data } = await api.get<
    ApiSuccessResponse<PaginatedList<OrganizationActivity>>
  >("/organizations/recent-activities", {
    params: {
      limit: params?.limit ?? 10,
      offset: params?.offset ?? 0,
    },
  });
  return data.data;
};

// ─── Onboarding Status ────────────────────────────────────────────────────────

export interface OnboardingStatus {
  has_completed_onboarding: boolean;
  needs_onboarding: boolean;
  has_pending_invitation: boolean;
  invitation_uuid: string | null;
  organization_uuid: string | null;
  role_code: string | null;
  message: string;
}

export interface OnboardingStatusResponse {
  success: boolean;
  message: string;
  data: OnboardingStatus;
}

export const getOnboardingStatus = async (): Promise<OnboardingStatus> => {
  const { data } = await api.get<OnboardingStatusResponse>(
    "/organizations/onboarding-status",
  );
  return data.data;
};

// ─── Re-export member types for convenience ───────────────────────────────────
export type {
  OrganizationMember,
  OrganizationInvitation,
  OrganizationActivity,
};
