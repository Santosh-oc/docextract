import type {
  DocumentOut,
  ExtractionFieldDraft,
  ExtractionOut,
  ExtractionResultResponse,
  ModelSettingsIn,
  ModelSettingsOut,
  TestConnectionResponse,
} from "../types";

// import.meta.env.BASE_URL is Vite's configured `base` (e.g. "/" locally, or
// "/workspace/<user>/<app>/" behind the DKubeX platform). Every API call must
// carry that prefix, or it 404s once the app is served under a base path.
const API_ROOT = `${import.meta.env.BASE_URL.replace(/\/$/, "")}/api`;

export class ApiError extends Error {
  detail?: string | null;
  status: number;

  constructor(message: string, status: number, detail?: string | null) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_ROOT}${path}`, init);
  if (!resp.ok) {
    let message = `Request failed with status ${resp.status}`;
    let detail: string | null | undefined;
    try {
      const body = await resp.json();
      if (body?.error) {
        message = body.error;
        detail = body.detail;
      } else if (body?.detail) {
        // FastAPI's default validation-error shape
        message = Array.isArray(body.detail)
          ? body.detail.map((d: { msg?: string }) => d.msg).join(", ")
          : String(body.detail);
      }
    } catch {
      // response wasn't JSON; fall back to the generic message
    }
    throw new ApiError(message, resp.status, detail);
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

function jsonInit(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export const settingsApi = {
  get: () => request<ModelSettingsOut>("/settings/model"),
  update: (payload: ModelSettingsIn) => request<ModelSettingsOut>("/settings/model", jsonInit("PUT", payload)),
  testConnection: () => request<TestConnectionResponse>("/settings/model/test", { method: "POST" }),
  fetchModels: (apiBaseUrl: string, apiKey: string) =>
    request<{ models: string[] }>(
      "/settings/model/models",
      jsonInit("POST", { api_base_url: apiBaseUrl, api_key: apiKey }),
    ),
};

export const documentsApi = {
  upload: async (file: File): Promise<DocumentOut> => {
    const form = new FormData();
    form.append("file", file);
    const result = await request<{ document: DocumentOut }>("/documents/upload", {
      method: "POST",
      body: form,
    });
    return result.document;
  },
  get: (documentId: string) => request<DocumentOut>(`/documents/${documentId}`),
  pageImageUrl: (documentId: string, pageNum: number) => `${API_ROOT}/documents/${documentId}/pages/${pageNum}`,
  downloadUrl: (documentId: string) => `${API_ROOT}/documents/${documentId}/download`,
  remove: (documentId: string) => request<void>(`/documents/${documentId}`, { method: "DELETE" }),
};

export const extractionsApi = {
  create: (documentId: string, fields: ExtractionFieldDraft[], instructions: string) =>
    request<ExtractionOut>(
      "/extractions",
      jsonInit("POST", {
        document_id: documentId,
        instructions,
        fields: fields.map((f) => ({
          name: f.name,
          display_name: f.display_name,
          description: f.description,
          data_type: f.data_type,
          required: f.required,
        })),
      }),
    ),
  getResult: (extractionId: string) => request<ExtractionResultResponse>(`/extractions/${extractionId}/result`),
  downloadJsonUrl: (extractionId: string) => `${API_ROOT}/extractions/${extractionId}/download/json`,
  downloadCsvUrl: (extractionId: string) => `${API_ROOT}/extractions/${extractionId}/download/csv`,
};
