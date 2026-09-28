import { DATA_TYPES, type DataType, type ExtractionFieldDraft } from "../types";

interface Props {
  fields: ExtractionFieldDraft[];
  onChange: (fields: ExtractionFieldDraft[]) => void;
}

function slugify(displayName: string, existing: Set<string>): string {
  const base =
    displayName
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "") || "field";
  let candidate = base;
  let i = 2;
  while (existing.has(candidate)) {
    candidate = `${base}_${i}`;
    i += 1;
  }
  return candidate;
}

export default function FieldEditor({ fields, onChange }: Props) {
  function addField() {
    const existingNames = new Set(fields.map((f) => f.name));
    onChange([
      ...fields,
      {
        id: crypto.randomUUID(),
        name: slugify("", existingNames),
        display_name: "",
        description: "",
        data_type: "String",
        required: false,
      },
    ]);
  }

  function updateField(id: string, patch: Partial<ExtractionFieldDraft>) {
    onChange(
      fields.map((f) => {
        if (f.id !== id) return f;
        const next = { ...f, ...patch };
        if (patch.display_name !== undefined) {
          const existingNames = new Set(fields.filter((o) => o.id !== id).map((o) => o.name));
          next.name = slugify(patch.display_name, existingNames);
        }
        return next;
      }),
    );
  }

  function removeField(id: string) {
    onChange(fields.filter((f) => f.id !== id));
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Fields to Extract</h3>
      </div>

      {fields.length === 0 && (
        <p className="rounded-md border border-dashed border-slate-300 px-4 py-6 text-center text-xs text-slate-400 dark:border-slate-700 dark:text-slate-500">
          No fields yet. Add at least one field to extract.
        </p>
      )}

      <div className="space-y-3">
        {fields.map((field) => (
          <div key={field.id} className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
            <div className="grid grid-cols-2 gap-3">
              <label className="col-span-2 block">
                <span className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Field Name</span>
                <input
                  type="text"
                  value={field.display_name}
                  onChange={(e) => updateField(field.id, { display_name: e.target.value })}
                  placeholder="e.g. Policy Number"
                  className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-400"
                />
              </label>

              <label className="col-span-2 block">
                <span className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Description</span>
                <input
                  type="text"
                  value={field.description}
                  onChange={(e) => updateField(field.id, { description: e.target.value })}
                  placeholder="Extract the policy number"
                  className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-400"
                />
              </label>

              <label className="block">
                <span className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Type</span>
                <select
                  value={field.data_type}
                  onChange={(e) => updateField(field.id, { data_type: e.target.value as DataType })}
                  className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-slate-400 dark:focus:ring-slate-400"
                >
                  {DATA_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex items-end gap-2 pb-1.5">
                <input
                  type="checkbox"
                  checked={field.required}
                  onChange={(e) => updateField(field.id, { required: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-300 dark:border-slate-600 dark:bg-slate-900"
                />
                <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Required</span>
              </label>
            </div>

            <div className="mt-2 flex justify-end">
              <button
                onClick={() => removeField(field.id)}
                className="text-xs font-medium text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={addField}
        className="w-full rounded-md border border-dashed border-slate-300 py-2 text-xs font-medium text-slate-600 hover:border-slate-400 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-400 dark:hover:border-slate-500 dark:hover:bg-slate-900"
      >
        + Add Field
      </button>
    </div>
  );
}
