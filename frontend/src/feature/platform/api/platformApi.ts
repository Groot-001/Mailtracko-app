import { api } from "../../../shared/api/axios";

interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface BillingPlanRecord {
  uuid: string;
  code: string;
  name: string;
  description?: string | null;
  currency: string;
  monthly_price_cents: number;
  annual_price_cents: number;
  trial_days: number;
  limits: Record<string, number>;
  features: string[];
  is_active: boolean;
  is_default: boolean;
  monthly_checkout_configured: boolean;
  annual_checkout_configured: boolean;
}

export interface BillingOverview {
  billing_enabled: boolean;
  subscription: null | {
    uuid: string;
    status: string;
    billing_cycle: "monthly" | "annual";
    seats: number;
    trial_ends_at?: string | null;
    current_period_end?: string | null;
    cancel_at_period_end: boolean;
    provider_managed: boolean;
    plan: BillingPlanRecord;
  };
  available_plans: BillingPlanRecord[];
  usage: Record<string, number>;
  limits: Record<string, number>;
  profile: null | {
    billing_email?: string | null;
    company_name?: string | null;
    tax_id?: string | null;
    address?: Record<string, string> | null;
    card_brand?: string | null;
    card_last4?: string | null;
    card_exp_month?: number | null;
    card_exp_year?: number | null;
  };
  invoices: Array<{
    uuid: string;
    number?: string | null;
    description?: string | null;
    amount_due_cents: number;
    amount_paid_cents: number;
    currency: string;
    status: string;
    hosted_invoice_url?: string | null;
    invoice_pdf_url?: string | null;
    paid_at?: string | null;
    created_at: string;
  }>;
}

export interface SuppressionRecord {
  uuid: string;
  email: string;
  reason: string;
  active: boolean;
  suppressed_at: string;
}

export interface AuditRecord {
  uuid: string;
  action: string;
  resource_type: string;
  resource_uuid?: string | null;
  metadata?: Record<string, unknown> | null;
  ip_address?: string | null;
  actor?: { name?: string | null; email?: string | null } | null;
  created_at: string;
}

export interface ApiKeyRecord {
  uuid: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  last_used_at?: string | null;
  expires_at?: string | null;
  revoked_at?: string | null;
  created_at: string;
}

export interface WebhookRecord {
  uuid: string;
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
  last_delivery_at?: string | null;
  last_status_code?: number | null;
  failure_count: number;
  created_at: string;
}

export interface NotificationPreferences {
  email_enabled: boolean;
  in_app_enabled: boolean;
  categories: Record<string, boolean>;
}

export const getBillingOverview = async (): Promise<BillingOverview> => {
  const { data } = await api.get<ApiEnvelope<BillingOverview>>("/billing/overview");
  return data.data;
};

export const createBillingCheckout = async (payload: {
  plan_code: string;
  billing_cycle: "monthly" | "annual";
  promotion_code?: string;
}): Promise<{ url: string }> => {
  const { data } = await api.post<ApiEnvelope<{ checkout_url: string }>>(
    "/billing/checkout",
    payload,
  );
  return { url: data.data.checkout_url };
};

export const createBillingPortal = async (): Promise<{ url: string }> => {
  const { data } = await api.post<ApiEnvelope<{ portal_url: string }>>("/billing/portal");
  return { url: data.data.portal_url };
};

export const changeBillingPlan = async (payload: {
  plan_code: string;
  billing_cycle: "monthly" | "annual";
}) => {
  const { data } = await api.post<
    ApiEnvelope<{ plan_code: string; billing_cycle: string; status: string }>
  >("/billing/change-plan", payload);
  return data.data;
};

export const cancelBillingSubscription = async () => {
  const { data } = await api.post<ApiEnvelope<{ cancel_at_period_end: boolean }>>(
    "/billing/cancel",
  );
  return data.data;
};

export const resumeBillingSubscription = async () => {
  const { data } = await api.post<ApiEnvelope<{ cancel_at_period_end: boolean }>>(
    "/billing/resume",
  );
  return data.data;
};

export const updateBillingProfile = async (payload: {
  billing_email?: string;
  company_name?: string;
  tax_id?: string;
  address?: Record<string, string>;
}) => {
  const { data } = await api.put<ApiEnvelope<Record<string, unknown>>>("/billing/profile", payload);
  return data.data;
};

export const getSuppressions = async (search?: string, limit = 10, offset = 0) => {
  const { data } = await api.get<ApiEnvelope<{ items: SuppressionRecord[]; total: number }>>(
    "/platform/suppressions",
    { params: { search: search || undefined, limit, offset } },
  );
  return data.data;
};

export const addSuppression = async (payload: { email: string; reason: string }) => {
  const { data } = await api.post<ApiEnvelope<SuppressionRecord>>(
    "/platform/suppressions",
    payload,
  );
  return data.data;
};

export const removeSuppression = async (uuid: string) => {
  const { data } = await api.delete<ApiEnvelope<{ uuid: string }>>(
    `/platform/suppressions/${uuid}`,
  );
  return data.data;
};

export const getAuditLogs = async (search?: string, limit = 10, offset = 0) => {
  const { data } = await api.get<ApiEnvelope<{ items: AuditRecord[]; total: number }>>(
    "/platform/audit-logs",
    { params: { search: search || undefined, limit, offset } },
  );
  return data.data;
};

export const getApiKeys = async () => {
  const { data } = await api.get<ApiEnvelope<{ items: ApiKeyRecord[] }>>("/platform/api-keys");
  return data.data;
};

export const createApiKey = async (payload: {
  name: string;
  scopes: string[];
  expires_at?: string;
}) => {
  const { data } = await api.post<
    ApiEnvelope<ApiKeyRecord & { key: string }>
  >("/platform/api-keys", payload);
  return data.data;
};

export const revokeApiKey = async (uuid: string) => {
  const { data } = await api.delete<ApiEnvelope<{ uuid: string }>>(`/platform/api-keys/${uuid}`);
  return data.data;
};

export const getWebhooks = async () => {
  const { data } = await api.get<ApiEnvelope<{ items: WebhookRecord[] }>>("/platform/webhooks");
  return data.data;
};

export const createWebhook = async (payload: { name: string; url: string; events: string[] }) => {
  const { data } = await api.post<
    ApiEnvelope<WebhookRecord & { secret: string }>
  >("/platform/webhooks", payload);
  return data.data;
};

export const deleteWebhook = async (uuid: string) => {
  const { data } = await api.delete<ApiEnvelope<{ uuid: string }>>(`/platform/webhooks/${uuid}`);
  return data.data;
};

export const getNotificationPreferences = async (): Promise<NotificationPreferences> => {
  const { data } = await api.get<ApiEnvelope<NotificationPreferences>>("/platform/preferences");
  return data.data;
};

export const saveNotificationPreferences = async (payload: NotificationPreferences) => {
  const { data } = await api.put<ApiEnvelope<NotificationPreferences>>(
    "/platform/preferences",
    payload,
  );
  return data.data;
};

export interface PlatformAccess {
  is_platform_admin: boolean;
  workspace_role: "owner" | "admin" | "member" | null;
  workspace_permissions: Record<string, boolean>;
  organization_uuid: string | null;
  feature_flags: Record<string, boolean>;
  maintenance?: { enabled?: boolean; message?: string; ends_at?: string | null } | null;
  support_email?: string | null;
  chatboq_widget_url?: string | null;
  integrations?: {
    google_login_configured: boolean;
    gmail_sender_configured: boolean;
    google_sheets_configured: boolean;
    email_verification_configured: boolean;
    cloudinary_configured: boolean;
    local_uploads_enabled: boolean;
  };
}

export interface SupportArticle {
  uuid: string;
  slug: string;
  title: string;
  category: string;
  summary?: string | null;
  content?: string;
  tags: string[];
  updated_at?: string | null;
}

export interface SupportTicket {
  uuid: string;
  subject: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  resolution?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export const getPlatformAccess = async (): Promise<PlatformAccess> => {
  const { data } = await api.get<ApiEnvelope<PlatformAccess>>("/platform/access");
  return data.data;
};

export const getSupportArticles = async (search?: string) => {
  const { data } = await api.get<
    ApiEnvelope<{
      items: SupportArticle[];
      total: number;
      categories: Array<{ name: string; count: number }>;
    }>
  >("/support/articles", { params: { search: search || undefined } });
  return data.data;
};

export const getSupportArticle = async (slug: string): Promise<SupportArticle> => {
  const { data } = await api.get<ApiEnvelope<SupportArticle>>(`/support/articles/${slug}`);
  return data.data;
};

export const getSupportTickets = async () => {
  const { data } = await api.get<ApiEnvelope<{ items: SupportTicket[]; total: number }>>(
    "/support/tickets",
  );
  return data.data;
};

export const createSupportTicket = async (payload: {
  subject: string;
  description: string;
  category: string;
  priority: "low" | "normal" | "high" | "urgent";
}) => {
  const { data } = await api.post<ApiEnvelope<SupportTicket>>("/support/tickets", payload);
  return data.data;
};

export interface AdminDashboard {
  users: { total: number; active: number };
  organizations: number;
  campaigns: number;
  support: { open_tickets: number };
  billing: {
    gross_revenue_cents: number;
    refunds_cents: number;
    net_revenue_cents: number;
    subscriptions: Record<string, number>;
  };
  risk: { open_abuse_events: number };
  infrastructure: { database: "healthy" | "unavailable"; redis: "healthy" | "unavailable" };
}

export const getAdminDashboard = async (): Promise<AdminDashboard> => {
  const { data } = await api.get<ApiEnvelope<AdminDashboard>>("/admin/dashboard");
  return data.data;
};

export const getAdminOrganizations = async (limit = 10, offset = 0) => {
  const { data } = await api.get<
    ApiEnvelope<{
      items: Array<{
        uuid: string;
        name: string;
        domain_email?: string | null;
        status: string;
        owner_email: string;
        subscription_status?: string | null;
        plan_name?: string | null;
        created_at: string;
      }>;
      total: number;
    }>
  >("/admin/organizations", { params: { limit, offset } });
  return data.data;
};

export const updateAdminOrganizationStatus = async (payload: {
  uuid: string;
  status: "active" | "suspended";
}) => {
  const { data } = await api.patch<ApiEnvelope<{ uuid: string; status: string }>>(
    `/admin/organizations/${payload.uuid}/status`,
    { status: payload.status },
  );
  return data.data;
};

export const deleteAdminOrganization = async (uuid: string) => {
  const { data } = await api.delete<ApiEnvelope<{ uuid: string; deleted: boolean }>>(
    `/admin/organizations/${uuid}`,
  );
  return data.data;
};

export interface AdminUser {
  uuid: string;
  full_name: string;
  email: string;
  is_active: boolean;
  email_verified_at?: string | null;
  last_login_at?: string | null;
  scheduled_deletion_at?: string | null;
  created_at: string;
}

export const getAdminUsers = async (search?: string, limit = 10, offset = 0) => {
  const { data } = await api.get<ApiEnvelope<{ items: AdminUser[]; total: number }>>(
    "/admin/users",
    { params: { search: search || undefined, limit, offset } },
  );
  return data.data;
};

export const updateAdminUserStatus = async (payload: {
  uuid: string;
  is_active: boolean;
}) => {
  const { data } = await api.patch<ApiEnvelope<{ uuid: string; is_active: boolean }>>(
    `/admin/users/${payload.uuid}/status`,
    { is_active: payload.is_active },
  );
  return data.data;
};

export const deleteAdminUser = async (uuid: string) => {
  const { data } = await api.delete<ApiEnvelope<{ uuid: string; deleted: boolean }>>(
    `/admin/users/${uuid}`,
  );
  return data.data;
};

export interface AdminBillingConfiguration {
  billing_enabled: boolean;
  mode: "unconfigured" | "test" | "live" | "configured";
  secret_key_configured: boolean;
  publishable_key_configured: boolean;
  webhook_secret_configured: boolean;
  api_version: string;
  automatic_tax: boolean;
  collect_billing_address: boolean;
  proration_behavior: string;
  webhook_path: string;
}

export interface AdminBillingPlan extends Omit<
  BillingPlanRecord,
  "monthly_checkout_configured" | "annual_checkout_configured"
> {
  display_order: number;
  stripe_monthly_price_id?: string | null;
  stripe_annual_price_id?: string | null;
}

export type AdminBillingPlanPayload = Omit<AdminBillingPlan, "uuid">;

export const getAdminBillingConfiguration = async (): Promise<AdminBillingConfiguration> => {
  const { data } = await api.get<ApiEnvelope<AdminBillingConfiguration>>(
    "/admin/billing/configuration",
  );
  return data.data;
};

export const getAdminPlans = async () => {
  const { data } = await api.get<ApiEnvelope<{ items: AdminBillingPlan[] }>>(
    "/admin/plans",
  );
  return data.data;
};

export const createAdminPlan = async (payload: AdminBillingPlanPayload) => {
  const { data } = await api.post<ApiEnvelope<AdminBillingPlan>>("/admin/plans", payload);
  return data.data;
};

export const updateAdminPlan = async (payload: {
  uuid: string;
  values: AdminBillingPlanPayload;
}) => {
  const { data } = await api.put<ApiEnvelope<AdminBillingPlan>>(
    `/admin/plans/${payload.uuid}`,
    payload.values,
  );
  return data.data;
};

export interface AppNotification {
  uuid: string;
  notification_type: string;
  title: string;
  body: string;
  action_url?: string | null;
  metadata?: Record<string, unknown> | null;
  read_at?: string | null;
  created_at: string;
}

export const getAppNotifications = async (unreadOnly = false) => {
  const { data } = await api.get<
    ApiEnvelope<{ items: AppNotification[]; total: number }>
  >("/platform/notifications", { params: { unread_only: unreadOnly } });
  return data.data;
};

export const markNotificationRead = async (uuid: string) => {
  const { data } = await api.post<ApiEnvelope<AppNotification>>(
    `/platform/notifications/${uuid}/read`,
  );
  return data.data;
};

export const markAllNotificationsRead = async () => {
  const { data } = await api.post<ApiEnvelope<{ updated: boolean }>>(
    "/platform/notifications/read-all",
  );
  return data.data;
};
