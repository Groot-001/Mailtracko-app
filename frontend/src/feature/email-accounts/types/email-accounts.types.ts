export type EmailAccountProvider = "gmail" | "smtp";
export type EmailAccountStatus =
  | "pending_verification"
  | "active"
  | "reconnect_required"
  | "disconnected";

export type HealthStatus = "unknown" | "healthy" | "unhealthy";

export interface HealthConnectionDetails {
  pass: boolean | null;
  points: number;
  note?: string;
}

export interface HealthDnsMxDetails {
  pass: boolean;
  records: string[];
  error?: string;
}

export interface HealthDnsSpfDetails {
  pass: boolean;
  record: string | null;
  error?: string;
}

export interface HealthDnsDkimDetails {
  pass: boolean;
  selectors: string[];
  error?: string;
}

export interface HealthDnsDmarcDetails {
  pass: boolean;
  record: string | null;
  error?: string;
}

export interface HealthDnsDetails {
  mx: HealthDnsMxDetails;
  spf: HealthDnsSpfDetails;
  dkim: HealthDnsDkimDetails;
  dmarc: HealthDnsDmarcDetails;
}

export interface HealthBlacklistDetails {
  pass: boolean | null;
  ip: string | null;
  listed_on: string[];
  error?: string;
  note?: string;
  points?: number;
}

export interface HealthDailyLimitDetails {
  used: number;
  limit: number;
  ratio: number;
  points: number;
}

export interface HealthDetails {
  connection?: HealthConnectionDetails;
  dns?: HealthDnsDetails;
  blacklist?: HealthBlacklistDetails;
  daily_limit?: HealthDailyLimitDetails;
  score: number;
  checked_at: string;
}

export interface EmailAccount {
  uuid: string;
  organization_id: number;
  provider: EmailAccountProvider;
  email: string;
  sender_name: string;
  status: EmailAccountStatus;
  health_status: HealthStatus;
  health_score: number;
  health_details: HealthDetails | null;
  daily_sent_count: number;
  last_sent_date: string | null;
  sending_limit: number;
  reply_to: string | null;
  signature: string | null;
  last_used_at: string | null;
  created_at: string;
}

export interface SMTPConnectPayload {
  email: string;
  sender_name: string;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password?: string;
  imap_host?: string;
  imap_port?: number;
  reply_to?: string;
  signature?: string;
}

export interface SMTPConnectResponse {
  uuid: string;
  email: string;
  provider: "smtp";
  status: "pending_verification";
  message: string;
}

export interface VerifyPayload {
  code: string;
}

export interface OAuthConnectPayload {
  provider: "gmail";
  account_uuid?: string; // For reconnecting
}

export interface OAuthConnectResponse {
  authorization_url: string;
}

export interface ConnectionTestResponse {
  uuid: string;
  email: string;
  provider: EmailAccountProvider;
  health_status: HealthStatus;
  health_score: number;
  health_details: HealthDetails;
  details: string;
}

export interface UpdateEmailAccountPayload {
  sender_name?: string;
  sending_limit?: number;
  reply_to?: string;
  signature?: string;
}
