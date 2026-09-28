import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { ApiError, documentsApi } from "../api/client";
import type { DocumentOut } from "../types";

interface Props {
  document: DocumentOut | null;
  onUploaded: (doc: DocumentOut) => void;
  onRemoved: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function PdfUpload({ document, onUploaded, onRemoved }: Props) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[], fileRejections: { file: File }[]) => {
      setError(null);
      if (fileRejections.length > 0) {
        setError("Only PDF documents are supported.");
        return;
      }
      const file = acceptedFiles[0];
      if (!file) return;
      if (file.type !== "application/pdf") {
        setError("Only PDF documents are supported.");
        return;
      }
      setUploading(true);
      try {
        const doc = await documentsApi.upload(file);
        onUploaded(doc);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Upload failed.");
      } finally {
        setUploading(false);
      }
    },
    [onUploaded],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: false,
    disabled: uploading || !!document,
  });

  if (document) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{document.original_filename}</p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {formatBytes(document.file_size)} · {document.page_count ?? "?"} page
              {document.page_count === 1 ? "" : "s"} · {document.status}
            </p>
          </div>
          <button
            onClick={onRemoved}
            className="whitespace-nowrap rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Remove / Replace
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
          isDragActive
            ? "border-slate-500 bg-slate-50 dark:border-slate-400 dark:bg-slate-900"
            : "border-slate-300 hover:border-slate-400 dark:border-slate-700 dark:hover:border-slate-500"
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
          {uploading ? "Uploading…" : "Drag & drop a PDF here"}
        </p>
        {!uploading && (
          <>
            <p className="my-2 text-xs text-slate-400 dark:text-slate-500">or</p>
            <span className="inline-block rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 dark:border-slate-700 dark:text-slate-300">
              Browse PDF
            </span>
          </>
        )}
      </div>
      {error && <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
