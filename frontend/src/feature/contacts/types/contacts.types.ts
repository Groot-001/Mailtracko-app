export interface ContactList {
  uuid: string;
  name: string;
  description: string | null;
  field_definitions: string[] | null;
  created_at: string;
  updated_at: string | null;
  contact_count: number;
  verified_count: number;
}

export interface Contact {
  uuid: string;
  email: string;
  metadata: Record<string, string | null>;
  subscribed: boolean;
  unsubscribed_at: string | null;
  last_contacted_at: string | null;
  status: "active" | "bounced" | "unsubscribed" | "suppressed" | "archived";
  verification_status:
    | "unverified"
    | "valid"
    | "invalid"
    | "catch-all"
    | "unknown"
    | "spamtrap"
    | "abuse"
    | "do_not_mail";
  verification_sub_status: string | null;
  verification_score: number | null;
  verification_details: Record<string, string | number | boolean | null> | null;
  verified_at: string | null;
  bounce_risk: "low" | "medium" | "high" | "critical" | null;
  last_bounced_at: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface ImportSuccessData {
  total: number;
  imported: number;
  updated: number;
  errors: { row: number; error: string }[];
  duplicates?: number;
  skipped?: number;
  reasons?: Record<string, number>;
  preview?: {
    headers: string[];
    rows: string[][];
  };
}

export interface SheetsOAuthInitResponse {
  auth_url: string;
}

export interface SheetTab {
  title: string;
  sheet_id: number;
  row_count: number;
}

export interface SheetsTabsResponse {
  tabs: SheetTab[];
}

export interface TimelineItem {
  uuid: string;
  activity_type:
    | "imported"
    | "merged"
    | "email_sent"
    | "email_opened"
    | "email_clicked"
    | "bounced"
    | "unsubscribed"
    | "manual_note";
  description: string;
  metadata: Record<string, string | null>;
  created_at: string;
}

export interface ListContactsParams {
  limit?: number;
  offset?: number;
  search?: string;
  subscribed?: boolean;
  company?: string;
  tag?: string;
  status?: Contact["status"];
  verification_status?: Contact["verification_status"];
  sort_by?: string;
  sort_order?: "asc" | "desc";
}
