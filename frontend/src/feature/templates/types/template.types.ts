import type { PaginatedResponse } from "../../../shared/types/api.types";

export type TemplateStatus = "draft" | "published" | "archived";

export interface EmailTemplate {
  uuid: string;
  organization_id: number | null;
  category_id: number | null;
  source_template_id: number | null;
  name: string;
  description: string | null;
  subject: string;
  preheader: string | null;
  from_name: string | null;
  from_email: string | null;
  tags: string[];
  template_type: "system" | "custom" | string;
  status: TemplateStatus | string;
  is_active: boolean;
  is_default: boolean;
  smart_personalization_enabled: boolean;
  published_at: string | null;
  archived_at: string | null;
  created_by_id: number | null;
  updated_by_id: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface EmailTemplateDetail extends EmailTemplate {
  body_html: string;
}

export interface TemplateAsset {
  uuid: string;
  template_id: number;
  organization_id: number | null;
  original_filename: string;
  file_url: string;
  content_type: string;
  file_size: number;
  asset_type: string;
  usage: string;
  is_active: boolean;
  created_at: string;
}

export interface TemplateCategory {
  id: number;
  uuid: string;
  organization_id: number | null;
  name: string;
  description: string | null;
  display_order: number;
  is_active: boolean;
}

export interface CreateTemplateCategoryPayload {
  name: string;
  description?: string | null;
  display_order?: number;
}

export interface TemplateDashboardSummary {
  total_templates: number;
  draft_templates: number;
  published_templates: number;
  archived_templates: number;
  total_categories: number;
  used_in_campaigns: number | null;
}

export interface TemplateListParams {
  status?: TemplateStatus | "";
  include_archived?: boolean;
  category_id?: number;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface TemplatePayload {
  name: string;
  subject: string;
  body_html: string;
  description?: string | null;
  preheader?: string | null;
  from_name?: string | null;
  from_email?: string | null;
  category_id?: number | null;
  tags?: string[];
  is_default?: boolean;
  smart_personalization_enabled?: boolean;
}

export interface TemplatePreviewPayload {
  subject: string;
  body_html: string;
  preheader?: string | null;
  variables?: Record<string, unknown>;
}

export interface TemplatePreviewResult {
  subject: string;
  preheader: string | null;
  body_html: string;
  variables: string[];
  unresolved_variables: string[];
  fallback_variables: string[];
}

export interface TestEmailPayload extends TemplatePreviewPayload {
  email_account_uuid: string;
  recipient_email: string;
  from_name?: string | null;
}

export type TemplateListResult = PaginatedResponse<EmailTemplate>;
