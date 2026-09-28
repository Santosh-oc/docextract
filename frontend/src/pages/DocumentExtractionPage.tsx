import { useEffect, useState } from "react";
import { ApiError, documentsApi, extractionsApi, settingsApi } from "../api/client";
import PdfUpload from "../components/PdfUpload";
import PdfPreview from "../components/PdfPreview";
import FieldEditor from "../components/FieldEditor";
import ExtractionProgress from "../components/ExtractionProgress";
import ExtractionResults from "../components/ExtractionResults";
import type { DocumentOut, ExtractionFieldDraft, ExtractionResultResponse } from "../types";

const DEFAULT_INSTRUCTIONS = `Extract only information that is present in the document.

Do not guess or hallucinate values.

If a requested field cannot be found, return null.

Preserve the value as it appears in the document unless
normalization is explicitly requested.`;

export default function DocumentExtractionPage() {
  const [document, setDocument] = useState<DocumentOut | null>(null);
  const [fields, setFields] = useState<ExtractionFieldDraft[]>([]);
  const [instructions, setInstructions] = useState(DEFAULT_INSTRUCTIONS);
  const [modelConfigured, setModelConfigured] = useState<boolean | null>(null);

  const [extracting, setExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [result, setResult] = useState<ExtractionResultResponse | null>(null);

  useEffect(() => {
    settingsApi
      .get()
      .then((s) => setModelConfigured(Boolean(s.api_base_url && s.model_name)))
      .catch(() => setModelConfigured(false));
  }, []);

  function reset() {
    setDocument(null);
    setResult(null);
    setExtractionError(null);
  }

  const validFields = fields.filter((f) => f.display_name.trim().length > 0);
  const canExtract = !!document && validFields.length > 0 && modelConfigured !== false && !extracting;

  async function handleExtract() {
    if (!document) return;
    setExtracting(true);
    setExtractionError(null);
    setResult(null);
    try {
      const extraction = await extractionsApi.create(document.id, validFields, instructions);
      const full = await extractionsApi.getResult(extraction.id);
      setResult(full);
    } catch (err) {
      setExtractionError(err instanceof ApiError ? err.message : "The extraction failed unexpectedly.");
    } finally {
      setExtracting(false);
    }
  }

  async function handleRemoveDocument() {
    if (document) {
      try {
        await documentsApi.remove(document.id);
      } catch {
        // best-effort cleanup; the user is replacing it either way
      }
    }
    reset();
  }

  let extractDisabledReason: string | null = null;
  if (!document) extractDisabledReason = "Upload a PDF document first.";
  else if (validFields.length === 0) extractDisabledReason = "Add at least one field to extract.";
  else if (modelConfigured === false) extractDisabledReason = "Configure the Vision Model in Settings first.";

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <PdfUpload document={document} onUploaded={setDocument} onRemoved={() => void handleRemoveDocument()} />
          <PdfPreview document={document} />
        </div>

        <div className="space-y-4">
          <FieldEditor fields={fields} onChange={setFields} />

          <div>
            <h3 className="mb-1 text-sm font-semibold text-slate-900 dark:text-slate-100">Additional Instructions</h3>
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={5}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-xs text-slate-700 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:focus:border-slate-400 dark:focus:ring-slate-400"
            />
          </div>

          <div>
            <button
              onClick={() => void handleExtract()}
              disabled={!canExtract}
              title={extractDisabledReason ?? undefined}
              className="w-full rounded-md bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
            >
              Extract Document
            </button>
            {extractDisabledReason && !extracting && (
              <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{extractDisabledReason}</p>
            )}
          </div>

          {extracting && <ExtractionProgress />}

          {extractionError && (
            <div className="rounded-md border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950">
              <p className="text-sm font-medium text-red-800 dark:text-red-300">Extraction Failed</p>
              <p className="mt-1 text-xs text-red-700 dark:text-red-400">{extractionError}</p>
              <button
                onClick={() => void handleExtract()}
                className="mt-3 rounded-md border border-red-300 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-100 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-900"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </div>

      {result && (
        <ExtractionResults
          result={result}
          onExtractAgain={() => void handleExtract()}
          onClear={() => setResult(null)}
        />
      )}
    </div>
  );
}
