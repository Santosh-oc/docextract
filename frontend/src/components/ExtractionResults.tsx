import { Fragment, type ReactNode, useState } from "react";
import { extractionsApi } from "../api/client";
import type { ExtractionResultResponse } from "../types";

const LOW_CONFIDENCE_THRESHOLD = 0.75;

interface Props {
  result: ExtractionResultResponse;
  onExtractAgain: () => void;
  onClear: () => void;
}

export default function ExtractionResults({ result, onExtractAgain, onClear }: Props) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  async function handleCopyJson() {
    await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const { extraction, results } = result;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Extraction Results</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {extraction.fields_extracted} extracted · {extraction.fields_not_found} not found
            {extraction.validation_failures > 0 && ` · ${extraction.validation_failures} validation issue(s)`}
            {extraction.processing_time_ms != null && ` · ${(extraction.processing_time_ms / 1000).toFixed(1)}s`}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ActionButton onClick={() => void handleCopyJson()}>{copied ? "Copied!" : "Copy JSON"}</ActionButton>
          <ActionLink href={extractionsApi.downloadJsonUrl(extraction.id)}>Download JSON</ActionLink>
          <ActionLink href={extractionsApi.downloadCsvUrl(extraction.id)}>Download CSV</ActionLink>
          <ActionButton onClick={onExtractAgain}>Extract Again</ActionButton>
          <ActionButton onClick={onClear} variant="danger">
            Clear
          </ActionButton>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500 dark:border-slate-800 dark:text-slate-400">
              <th className="py-2 pr-4">Field</th>
              <th className="py-2 pr-4">Value</th>
              <th className="py-2 pr-4">Confidence</th>
              <th className="py-2 pr-4">Page</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => {
              const lowConfidence = r.confidence != null && r.confidence < LOW_CONFIDENCE_THRESHOLD;
              const isExpanded = expanded === r.id;
              return (
                <Fragment key={r.id}>
                  <tr
                    className="cursor-pointer border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/60"
                    onClick={() => setExpanded(isExpanded ? null : r.id)}
                  >
                    <td className="py-2 pr-4 font-medium text-slate-900 dark:text-slate-100">{r.field_display_name}</td>
                    <td className="py-2 pr-4">
                      {r.value == null ? (
                        <span className="text-slate-400 italic dark:text-slate-600">Not Found</span>
                      ) : (
                        <div>
                          <span className="text-slate-900 dark:text-slate-100">{String(r.value)}</span>
                          {lowConfidence && (
                            <p className="text-xs text-amber-600 dark:text-amber-400">
                              ⚠ Low Confidence: {Math.round((r.confidence ?? 0) * 100)}%
                            </p>
                          )}
                          {r.validation_status === "INVALID_FORMAT" && (
                            <p className="text-xs text-red-600 dark:text-red-400">⚠ Does not match expected format</p>
                          )}
                          {r.validation_status === "MISSING_REQUIRED" && (
                            <p className="text-xs text-red-600 dark:text-red-400">⚠ Required field missing</p>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="py-2 pr-4 text-slate-600 dark:text-slate-400">
                      {r.confidence != null ? `${Math.round(r.confidence * 100)}%` : "—"}
                    </td>
                    <td className="py-2 pr-4 text-slate-600 dark:text-slate-400">{r.page ?? "—"}</td>
                  </tr>
                  {isExpanded && r.evidence && (
                    <tr className="border-b border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-950">
                      <td colSpan={4} className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400">
                        <p className="font-medium text-slate-500 dark:text-slate-400">Evidence</p>
                        <p className="mt-1 italic">&ldquo;{r.evidence}&rdquo;</p>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ActionButton({
  children,
  onClick,
  variant = "default",
}: {
  children: ReactNode;
  onClick: () => void;
  variant?: "default" | "danger";
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md border px-3 py-1.5 text-xs font-medium ${
        variant === "danger"
          ? "border-red-200 text-red-600 hover:bg-red-50 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950"
          : "border-slate-300 text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
      }`}
    >
      {children}
    </button>
  );
}

function ActionLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
    >
      {children}
    </a>
  );
}
