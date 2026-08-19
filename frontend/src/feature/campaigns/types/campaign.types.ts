import type { PaginatedResponse } from "../../../shared/types/api.types";

export type CampaignType = "regular" | "sequence" | "ab_test";
export type CampaignStatus =
  | "draft"
  | "ready"
  | "scheduled"
  | "launching"
  | "running"
  | "paused"
  | "completed"
  | "cancelled"
  | "failed"
  | "archived";

export type CampaignGoal =
  | "sales"
  | "lead_generation"
  | "outreach"
  | "follow_up"
  | "newsletter"
  | "custom";

export type CampaignPriority = "low" | "normal" | "high" | "critical";
export type CampaignStep = "setup" | "audience" | "sender" | "content" | "schedule" | "review" | "launch";
export type DelayUnit = "minutes" | "hours" | "days" | "weeks";
export type ABWinnerMetric = "delivery_rate" | "open_rate" | "click_rate" | "reply_rate";

export interface Campaign {
  uuid: string;
  organization_id: number;
  name: string;
  description: string | null;
  campaign_type: CampaignType | string;
  goal: string;
  priority: string;
  status: CampaignStatus | string;
  current_step: CampaignStep | string;
  email_account_uuid: string | null;
  email_account_email: string | null;
  template_uuid: string | null;
  template_name: string | null;
  contact_list_uuid: string | null;
  contact_list_name: string | null;
  schedule_type: string;
  timezone: string;
  scheduled_at: string | null;
  sending_window_start: string | null;
  sending_window_end: string | null;
  sending_days: number[];
  daily_limit: number | null;
  batch_size: number;
  total_recipients: number;
  sent_count: number;
  failed_count: number;
  skipped_count: number;
  progress_percentage: number;
  launched_at: string | null;
  paused_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  archived_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface CampaignSummary {
  total_campaigns: number;
  active: number;
  scheduled: number;
  paused: number;
  drafts: number;
  completed: number;
  failed: number;
}

export interface CampaignListParams {
  search?: string;
  status?: CampaignStatus | "";
  campaign_type?: CampaignType | "";
  email_account_uuid?: string;
  include_archived?: boolean;
  limit?: number;
  offset?: number;
}

export interface CreateCampaignPayload {
  name: string;
  description?: string | null;
  campaign_type: CampaignType;
  goal: CampaignGoal;
  priority?: CampaignPriority;
  timezone?: string;
  sending_window_start?: string | null;
  sending_window_end?: string | null;
  sending_days?: number[];
  email_account_uuid?: string | null;
  template_uuid?: string | null;
  contact_list_uuid?: string | null;
  daily_limit?: number | null;
  batch_size?: number;
}

export interface UpdateCampaignPayload {
  name?: string;
  description?: string | null;
  goal?: CampaignGoal;
  priority?: CampaignPriority;
  current_step?: CampaignStep;
  timezone?: string;
  sending_window_start?: string | null;
  sending_window_end?: string | null;
  sending_days?: number[];
  email_account_uuid?: string | null;
  template_uuid?: string | null;
  contact_list_uuid?: string | null;
  daily_limit?: number | null;
  batch_size?: number;
}

export interface SequenceStepPayload {
  step_order: number;
  step_type: "email" | "delay";
  template_uuid?: string | null;
  subject_override?: string | null;
  body_html_override?: string | null;
  delay_value?: number | null;
  delay_unit?: DelayUnit | null;
  is_enabled: boolean;
}

export interface ConfigureSequencePayload {
  stop_on_reply: boolean;
  stop_on_unsubscribe: true;
  stop_on_click: boolean;
  stop_on_meeting: boolean;
  custom_stop_events: string[];
  steps: SequenceStepPayload[];
}

export interface SequenceResponse {
  uuid: string;
  status: string;
  stop_on_reply: boolean;
  stop_on_unsubscribe: boolean;
  stop_on_click: boolean;
  stop_on_meeting: boolean;
  custom_stop_events: string[];
  total_steps: number;
  steps: Array<SequenceStepPayload & { uuid: string; template_name?: string | null }>;
}

export interface SequencePreviewStep {
  step_order: number;
  step_type: "email" | "delay" | string;
  due_at: string;
  template_uuid: string | null;
  delay_value: number | null;
  delay_unit: string | null;
}

export interface SequencePreview {
  starts_at: string;
  completes_at: string;
  steps: SequencePreviewStep[];
}

export interface ABVariantPayload {
  variant_type: "a" | "b";
  name: string;
  template_uuid?: string | null;
  subject_override?: string | null;
  body_html_override?: string | null;
  allocation_percentage: number;
}

export interface ConfigureABTestPayload {
  test_percentage: number;
  winner_metric: ABWinnerMetric;
  auto_select_winner: boolean;
  minimum_sample_size: number;
  test_duration_hours: number | null;
  variants: [ABVariantPayload, ABVariantPayload];
}

export interface ABTestResponse {
  uuid: string;
  status: string;
  test_percentage: number;
  winner_metric: ABWinnerMetric | string;
  auto_select_winner: boolean;
  minimum_sample_size: number;
  test_duration_hours: number | null;
  started_at: string | null;
  winner_selected_at: string | null;
  winner_variant_uuid: string | null;
  sampled_recipient_count: number;
  holdout_recipient_count: number;
  released_recipient_count: number;
  variants: Array<
    ABVariantPayload & {
      uuid: string;
      template_name?: string | null;
      sent_count: number;
      delivered_count: number;
      opened_count: number;
      clicked_count: number;
      replied_count: number;
      failed_count: number;
    }
  >;
}

export interface CampaignReview {
  ready: boolean;
  errors: string[];
  warnings: string[];
  audience: Record<string, number>;
}

export interface CampaignRecipient {
  uuid: string;
  contact_id: number | null;
  email: string;
  ab_test_sampled: boolean;
  status: string;
  current_step_order: number;
  attempt_count: number;
  next_attempt_at: string | null;
  provider_message_id: string | null;
  last_error_code: string | null;
  last_error_message: string | null;
  stop_reason: string | null;
  stopped_at: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  failed_at: string | null;
  bounced_at: string | null;
  opened_at: string | null;
  clicked_at: string | null;
  replied_at: string | null;
  unsubscribed_at: string | null;
  created_at: string | null;
}

export interface CampaignAnalytics {
  campaign_uuid: string;
  total_recipients: number;
  pending: number;
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  replied: number;
  bounced: number;
  failed: number;
  unsubscribed: number;
  skipped: number;
  delivery_rate: number;
  open_rate: number;
  click_rate: number;
  reply_rate: number;
  data_fresh_as_of: string;
}

export type CampaignListResult = PaginatedResponse<Campaign>;
export type CampaignRecipientListResult = PaginatedResponse<CampaignRecipient>;
