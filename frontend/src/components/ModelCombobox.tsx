import { useMemo, useState } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  models: string[];
  loading: boolean;
  onFetchModels: () => void;
}

export default function ModelCombobox({ value, onChange, models, loading, onFetchModels }: Props) {
  const [open, setOpen] = useState(false);

  const filtered = useMemo(() => {
    if (!value) return models;
    const lower = value.toLowerCase();
    return models.filter((m) => m.toLowerCase().includes(lower));
  }, [models, value]);

  return (
    <div className="relative">
      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder="e.g. Qwen3-VL-32B-Instruct"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-400"
        />
        <button
          type="button"
          onClick={onFetchModels}
          disabled={loading}
          className="whitespace-nowrap rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          {loading ? "Fetching…" : "Fetch Models"}
        </button>
      </div>
      {open && filtered.length > 0 && (
        <ul className="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-md border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900">
          {filtered.map((m) => (
            <li
              key={m}
              className="cursor-pointer px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
              onMouseDown={() => {
                onChange(m);
                setOpen(false);
              }}
            >
              {m}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
