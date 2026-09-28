import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { ApiError, settingsApi } from "../api/client";
import ModelCombobox from "../components/ModelCombobox";
import type { ModelSettingsIn, Provider, TestConnectionResponse } from "../types";

const EMPTY: ModelSettingsIn = {
  provider: "openai_compatible",
  api_base_url: "",
  api_key: "",
  model_name: "",
  temperature: 0,
  max_tokens: 4096,
  timeout: 120,
  pdf_render_dpi: 150,
};

function dkubexDefaultBaseUrl(): string {
  return `${window.location.protocol}//${window.location.host}/securellm/v1`;
}

export default function SettingsPage() {
  const [form, setForm] = useState<ModelSettingsIn>(EMPTY);
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [fetchingModels, setFetchingModels] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestConnectionResponse | null>(null);

  useEffect(() => {
    settingsApi
      .get()
      .then((data) => {
        setForm({
          provider: data.provider as Provider,
          api_base_url: data.api_base_url,
          api_key: "",
          model_name: data.model_name,
          temperature: data.temperature,
          max_tokens: data.max_tokens,
          timeout: data.timeout,
          pdf_render_dpi: data.pdf_render_dpi,
        });
        setApiKeyConfigured(data.api_key_configured);
      })
      .catch(() => void 0)
      .finally(() => setLoading(false));
  }, []);

  function update<K extends keyof ModelSettingsIn>(key: K, value: ModelSettingsIn[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setTestResult(null);
    setSaveMessage(null);
  }

  function handleProviderChange(provider: Provider) {
    setForm((prev) => {
      const shouldAutofill = provider === "dkubex" && !prev.api_base_url;
      return {
        ...prev,
        provider,
        api_base_url: shouldAutofill ? dkubexDefaultBaseUrl() : prev.api_base_url,
      };
    });
  }

  async function save(): Promise<boolean> {
    setSaving(true);
    setSaveMessage(null);
    try {
      const result = await settingsApi.update(form);
      setApiKeyConfigured(result.api_key_configured);
      setForm((prev) => ({ ...prev, api_key: "" }));
      setSaveMessage("Settings saved.");
      return true;
    } catch (err) {
      setSaveMessage(err instanceof ApiError ? `Failed to save: ${err.message}` : "Failed to save settings.");
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function handleFetchModels() {
    setFetchingModels(true);
    setModelsError(null);
    try {
      const { models } = await settingsApi.fetchModels(form.api_base_url, form.api_key || "");
      setModels(models);
    } catch (err) {
      setModelsError(err instanceof ApiError ? err.message : "Could not fetch models.");
    } finally {
      setFetchingModels(false);
    }
  }

  async function handleTestConnection() {
    const saved = await save();
    if (!saved) return;
    setTesting(true);
    setTestResult(null);
    try {
      const result = await settingsApi.testConnection();
      setTestResult(result);
    } catch (err) {
      setTestResult({
        success: false,
        model: null,
        response_time_seconds: null,
        message: err instanceof ApiError ? err.message : "Connection test failed.",
      });
    } finally {
      setTesting(false);
    }
  }

  if (loading) {
    return <div className="text-sm text-slate-500 dark:text-slate-400">Loading settings…</div>;
  }

  return (
    <div className="max-w-2xl space-y-8">
      <section>
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Provider</h2>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <ProviderCard
            label="OpenAI Compatible"
            description="OpenAI, vLLM, or any OpenAI-compatible vision endpoint."
            active={form.provider === "openai_compatible"}
            onClick={() => handleProviderChange("openai_compatible")}
          />
          <ProviderCard
            label="DKubeX (SecureLLM)"
            description="This platform's built-in SecureLLM gateway."
            active={form.provider === "dkubex"}
            onClick={() => handleProviderChange("dkubex")}
          />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Configuration</h2>

        <Field label="API Base URL">
          <input
            type="text"
            value={form.api_base_url}
            onChange={(e) => update("api_base_url", e.target.value)}
            placeholder="http://localhost:8000/v1"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-400"
          />
        </Field>

        <Field label="API Key">
          <input
            type="password"
            value={form.api_key}
            onChange={(e) => update("api_key", e.target.value)}
            placeholder={apiKeyConfigured ? "•••••••••••••• (configured — leave blank to keep)" : "Not configured"}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-400"
          />
        </Field>

        <Field label="Model">
          <ModelCombobox
            value={form.model_name}
            onChange={(v) => update("model_name", v)}
            models={models}
            loading={fetchingModels}
            onFetchModels={handleFetchModels}
          />
          {modelsError && <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">{modelsError}</p>}
        </Field>

        <div className="grid grid-cols-3 gap-4">
          <Field label="Temperature">
            <input
              type="number"
              step="0.1"
              min={0}
              max={2}
              value={form.temperature}
              onChange={(e) => update("temperature", Number(e.target.value))}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-400"
            />
          </Field>
          <Field label="Max Tokens">
            <input
              type="number"
              min={1}
              value={form.max_tokens}
              onChange={(e) => update("max_tokens", Number(e.target.value))}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-400"
            />
          </Field>
          <Field label="Timeout (seconds)">
            <input
              type="number"
              min={1}
              value={form.timeout}
              onChange={(e) => update("timeout", Number(e.target.value))}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-400"
            />
          </Field>
        </div>

        <Field label="PDF Rendering DPI">
          <input
            type="number"
            min={72}
            max={600}
            value={form.pdf_render_dpi}
            onChange={(e) => update("pdf_render_dpi", Number(e.target.value))}
            className="w-40 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-400"
          />
        </Field>
      </section>

      <section className="flex items-center gap-3">
        <button
          onClick={() => void save()}
          disabled={saving}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
        >
          {saving ? "Saving…" : "Save Settings"}
        </button>
        <button
          onClick={() => void handleTestConnection()}
          disabled={testing || saving}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          {testing ? "Testing…" : "Test Connection"}
        </button>
        {saveMessage && <span className="text-xs text-slate-500 dark:text-slate-400">{saveMessage}</span>}
      </section>

      {testResult && (
        <div
          className={`rounded-md border px-4 py-3 text-sm ${
            testResult.success
              ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-300"
              : "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-300"
          }`}
        >
          <p className="font-medium">{testResult.success ? "✓ Connection successful" : "✗ Connection failed"}</p>
          {testResult.model && <p>Model: {testResult.model}</p>}
          {testResult.response_time_seconds != null && <p>Response time: {testResult.response_time_seconds}s</p>}
          {testResult.message && <p>{testResult.message}</p>}
        </div>
      )}
    </div>
  );
}

function ProviderCard({
  label,
  description,
  active,
  onClick,
}: {
  label: string;
  description: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg border p-4 text-left transition-colors ${
        active
          ? "border-slate-900 bg-slate-900/5 dark:border-slate-100 dark:bg-slate-100/10"
          : "border-slate-200 hover:border-slate-300 dark:border-slate-800 dark:hover:border-slate-600"
      }`}
    >
      <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{label}</p>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{description}</p>
    </button>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">{label}</span>
      {children}
    </label>
  );
}
