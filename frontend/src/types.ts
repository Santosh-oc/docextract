export type DataType =
  | "String"
  | "Integer"
  | "Decimal"
  | "Date"
  | "Boolean"
  | "Email"
  | "Phone"
  | "Currency";

export const DATA_TYPES: DataType[] = [
  "String",
  "Integer",
  "Decimal",
  "Date",
  "Boolean",
  "Email",
  "Phone",
  "Currency",
];

export interface ExtractionFieldDraft {
  id: string; // client-only key for React lists
  name: string;
  display_name: string;
  description: string;
  data_type: DataType;
  required: boolean;
}

export interface DocumentOut {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  page_count: number | null;
  document_type: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ExtractionOut {
  id: string;
  document_id: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  model_provider: string;
  model_name: string;
  instructions: string | null;
  processing_time_ms: number | null;
  fields_requested: number;
  fields_extracted: number;
  fields_not_found: number;
  validation_failures: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ExtractionResultOut {
  id: string;
  field_id: string;
  field_name: string;
  field_display_name: string;
  value: string | number | boolean | null;
  normalized_value: string | number | boolean | null;
  confidence: number | null;
  status: string;
  page: number | null;
  document_section: string | null;
  evidence: string | null;
  bounding_box: Record<string, unknown> | null;
  validation_status: string | null;
  is_verified: boolean;
  is_user_edited: boolean;
  original_value: string | number | boolean | null;
  edited_value: string | number | boolean | null;
}

export interface ExtractionResultResponse {
  extraction: ExtractionOut;
  results: ExtractionResultOut[];
}

export type Provider = "openai_compatible" | "dkubex";

export interface ModelSettingsOut {
  provider: Provider;
  api_base_url: string;
  api_key_configured: boolean;
  model_name: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
  pdf_render_dpi: number;
}

export interface ModelSettingsIn {
  provider: Provider;
  api_base_url: string;
  api_key?: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
  pdf_render_dpi: number;
}

export interface TestConnectionResponse {
  success: boolean;
  model: string | null;
  response_time_seconds: number | null;
  message: string | null;
}

export interface ApiErrorBody {
  error: string;
  detail?: string | null;
}
