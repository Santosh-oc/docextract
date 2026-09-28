import { useState } from "react";
import { documentsApi } from "../api/client";
import type { DocumentOut } from "../types";

interface Props {
  document: DocumentOut | null;
}

export default function PdfPreview({ document }: Props) {
  const [page, setPage] = useState(1);
  const [zoom, setZoom] = useState(1);

  if (!document) {
    return (
      <div className="flex h-80 items-center justify-center rounded-lg border border-slate-200 bg-white text-sm text-slate-400 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-500">
        Upload a PDF to preview it here.
      </div>
    );
  }

  const pageCount = document.page_count ?? 1;
  const clampedPage = Math.min(Math.max(page, 1), pageCount);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">PDF Preview</h3>
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}
            className="rounded border border-slate-300 px-2 py-1 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            −
          </button>
          <span className="w-10 text-center text-slate-500 dark:text-slate-400">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => setZoom((z) => Math.min(2.5, z + 0.25))}
            className="rounded border border-slate-300 px-2 py-1 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            +
          </button>
        </div>
      </div>

      <div className="max-h-[32rem] overflow-auto rounded border border-slate-100 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-950">
        <img
          src={documentsApi.pageImageUrl(document.id, clampedPage)}
          alt={`Page ${clampedPage}`}
          style={{ width: `${zoom * 100}%` }}
          className="mx-auto"
        />
      </div>

      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-slate-500 dark:text-slate-400">
          Page {clampedPage} of {pageCount}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={clampedPage <= 1}
            className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Previous
          </button>
          <button
            onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
            disabled={clampedPage >= pageCount}
            className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
