import { type ReactNode, useState } from "react";
import SettingsPage from "./pages/SettingsPage";
import DocumentExtractionPage from "./pages/DocumentExtractionPage";

type Tab = "settings" | "extraction";

export default function App() {
  const [tab, setTab] = useState<Tab>("settings");

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Document Extraction</h1>
          <nav className="flex gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800">
            <TabButton active={tab === "settings"} onClick={() => setTab("settings")}>
              Settings
            </TabButton>
            <TabButton active={tab === "extraction"} onClick={() => setTab("extraction")}>
              Document Extraction
            </TabButton>
          </nav>
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-7xl px-6 py-6">
        {tab === "settings" ? <SettingsPage /> : <DocumentExtractionPage />}
      </main>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
        active
          ? "bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-slate-100"
          : "text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
      }`}
    >
      {children}
    </button>
  );
}
