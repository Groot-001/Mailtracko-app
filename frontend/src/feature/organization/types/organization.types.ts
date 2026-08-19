export type RoleCode = "owner" | "admin" | "member";
export type MemberStatus = "active" | "inactive" | "removed";
export type InvitationStatus =
  | "pending"
  | "accepted"
  | "declined"
  | "revoked"
  | "expired";
export type OrganizationStatus = "active" | "suspended";

// ─── Core Entities ────────────────────────────────────────────────────────────

export interface Organization {
  uuid: string;
  name: string;
  website_url: string | null;
  org_size: string | null;
  monthly_email_volume: string | null;
  domain_email: string | null;
  org_logo: string | null;
  description: string | null;
  industry_sector: string | null;
  source: string | null;
  theme: "light" | "dark";
  timezone: string;
  status: OrganizationStatus;
  owner_id: number;
  created_at: string;
  updated_at: string;
  deletion_requested_at: string | null;
  deletion_requested_by_id: number | null;
  scheduled_deletion_at: string | null;
}

export interface OrganizationMemberUser {
  uuid: string;
  email: string;
  full_name: string | null;
  avatar: string | null;
  avatar_bg: string | null;
}

export interface OrganizationMember {
  id: number;
  uuid: string;
  organization_id: number;
  user_id: number;
  role_code: RoleCode;
  status: MemberStatus;
  invited_by_id: number | null;
  joined_at: string | null;
  permissions: Record<string, boolean>;
  presence: "online" | "offline";
  last_active_at: string | null;
  user: OrganizationMemberUser | null;
}

export interface OrganizationInvitation {
  uuid: string;
  email: string;
  role_code: RoleCode;
  status: InvitationStatus;
  invited_by_id: number;
  expires_at: string;
  created_at?: string | null;
  updated_at?: string | null;
  accepted_at: string | null;
  declined_at: string | null;
  revoked_at: string | null;
}

export interface OrganizationActivity {
  uuid: string;
  activity_type: string;
  title: string;
  actor_user_id: number | null;
  target_user_id: number | null;
  target_email: string | null;
  created_at: string;
}

// ─── Paginated Lists ──────────────────────────────────────────────────────────

export interface PaginatedList<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export type MemberList = PaginatedList<OrganizationMember>;
export type InvitationList = PaginatedList<OrganizationInvitation>;

// ─── Request Payloads ─────────────────────────────────────────────────────────

export interface InviteMemberPayload {
  email: string;
  role_code: RoleCode;
}

export interface EditOrganizationPayload {
  name?: string;
  website_url?: string | null;
  org_size?: string;
  monthly_email_volume?: string;
  domain_email?: string | null;
  org_logo?: string | null;
  description?: string;
  industry_sector?: string;
  theme?: "light" | "dark";
  timezone?: string;
}

// ─── API Response Envelopes ───────────────────────────────────────────────────

export interface ApiSuccessResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

// ─── UI-only types ────────────────────────────────────────────────────────────

export type NotificationTab = "system" | "email";

export interface PermissionRow {
  label: string;
  icon: string;
  owner: boolean;
  admin: boolean;
  member: boolean;
}

export interface RoleDefinition {
  code: RoleCode;
  label: string;
  description: string;
  isDefault?: boolean;
  permissions: string[];
}

// organization.types.ts — add
export interface OrganizationDeletionSummary {
  organization_uuid: string;
  organization_name: string;
  grace_period_days: number;
  data_summary: {
    team_members: number;
    active_members: number;
    pending_invitations: number;
    campaigns: number;
    stored_contacts: number;
    files_and_attachments: number;
  };
}
