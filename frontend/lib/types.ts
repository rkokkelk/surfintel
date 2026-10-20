export type SourceType = "rss" | "html" | "gh" | "custom_module";

export interface VersionInfo {
  version: string;
  commit: string;
}

export interface Source {
  id: string;
  name: string;
  type: SourceType;
  favicon: string;
  config: Record<string, unknown>;
  enabled: boolean;
  enrich_cve: boolean;
  enrich_cpe: boolean;
  enrich_mitre: boolean;
  enrich_ai: boolean;
  poll_interval_seconds: number;
  last_polled_at: string | null;
}

export interface ItemEnrichment {
  module_name: string;
  module_version: string;
  data: Record<string, unknown>;
}

export interface Item {
  id: string;
  source_id: string;
  url: string;
  title: string | null;
  description: string | null;
  published_at: string | null;
  status: string;
  last_changed_at: string | null;
  created_at: string;
  source: Source;
  enrichments: ItemEnrichment[];
  max_cvss_score: number | null;
  max_epss_score: number | null;
  in_kev: boolean;
}

export interface ItemDetail extends Item {
  extracted_text: string | null;
}

export interface Cve {
  cve_id: string;
  title: string | null;
  cvss_v3_score: number | null;
  cvss_v4_score: number | null;
  epss_score: number | null;
  in_kev: boolean;
  fetched_at: string | null;
}

export interface CveReference {
  url: string;
  tags: string[];
}

export interface CveLinkedItem {
  id: string;
  title: string | null;
  url: string;
  published_at: string | null;
}

export interface CveDetail extends Cve {
  description: string | null;
  cvss_v3_vector: string | null;
  cvss_v4_vector: string | null;
  kev_date_added: string | null;
  cpes: string[];
  weaknesses: string[];
  references: CveReference[];
  items: CveLinkedItem[];
}

export type AlertField =
  | "vendor"
  | "product"
  | "severity"
  | "category"
  | "cve_id"
  | "source"
  | "tag"
  | "keyword"
  | "cvss_score"
  | "epss_score"
  | "kev"
  | "ttp"
  | "victim_category"
  | "victim_country"
  | "actor";

export interface AlertCondition {
  id: string;
  field: AlertField;
  values: string[];
}

export interface AlertChannel {
  id: string;
  label: string;
  apprise_url_masked: string;
  enabled: boolean;
}

export interface AlertRule {
  id: string;
  organization_id: string;
  name: string;
  status: "active" | "paused";
  created_at: string;
  conditions: AlertCondition[];
  channels: AlertChannel[];
  message_template: string | null;
}

// Computed client-side from the plain Item[] GET /alerts/{id}/items returns
// (see lib/dashboard-stats.ts) — the API hands over matched items only, no
// aggregation.
export interface AlertDashboardDayCount {
  date: string;
  count: number;
}

export interface AlertDashboardSourceCount {
  source_name: string;
  source_favicon: string | null;
  count: number;
}

export interface AlertTestMatch {
  item_id: string;
  title: string | null;
  url: string;
  source_name: string;
  published_at: string | null;
  message_preview: string;
}
