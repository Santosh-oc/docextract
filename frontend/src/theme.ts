const THEME_KEY = "dkubex-ui-theme";

type StoredTheme = "dark" | "light" | "system";

function resolveTheme(stored: string | null): "dark" | "light" {
  const value = (stored as StoredTheme) || "dark";
  if (value === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return value === "light" ? "light" : "dark";
}

function applyTheme(resolved: "dark" | "light") {
  document.documentElement.classList.toggle("dark", resolved === "dark");
}

/** Sync with the DKubeX platform's theme toggle. Never introduce a second theme key —
 * `dkubex-ui-theme` in localStorage is the only source of truth, default "dark". */
export function initTheme() {
  applyTheme(resolveTheme(localStorage.getItem(THEME_KEY)));

  window.addEventListener("storage", (e) => {
    if (e.key === THEME_KEY) {
      applyTheme(resolveTheme(e.newValue));
    }
  });

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if ((localStorage.getItem(THEME_KEY) as StoredTheme | null) === "system") {
      applyTheme(resolveTheme("system"));
    }
  });
}
