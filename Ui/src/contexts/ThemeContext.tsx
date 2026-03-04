import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";

export type ThemeMode = "system" | "dark" | "light";

type ThemeContextValue = {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  effectiveTheme: "dark" | "light";
  cycleMode: () => void;
};

const STORAGE_KEY = "crunchy-theme-mode";

const getStoredMode = (): ThemeMode => {
  if (typeof window === "undefined") return "system";
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "dark" || stored === "light" || stored === "system")
    return stored;
  return "system";
};

const getSystemTheme = (): "dark" | "light" =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function useThemeMode() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useThemeMode must be used within ThemeContextProvider");
  return ctx;
}

export function ThemeContextProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(getStoredMode);
  const [systemTheme, setSystemTheme] = useState<"dark" | "light">(getSystemTheme);

  const effectiveTheme = useMemo((): "dark" | "light" => {
    if (mode === "system") return systemTheme;
    return mode;
  }, [mode, systemTheme]);

  const setMode = useCallback((next: ThemeMode) => {
    setModeState(next);
    if (typeof window !== "undefined") localStorage.setItem(STORAGE_KEY, next);
  }, []);

  const cycleMode = useCallback(() => {
    setModeState((prev) => {
      const next: ThemeMode =
        prev === "system" ? "dark" : prev === "dark" ? "light" : "system";
      if (typeof window !== "undefined")
        localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (effectiveTheme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [effectiveTheme]);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => setSystemTheme(media.matches ? "dark" : "light");
    media.addEventListener("change", handler);
    return () => media.removeEventListener("change", handler);
  }, []);

  const muiTheme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: effectiveTheme,
          primary: { main: "#2563eb" },
        },
      }),
    [effectiveTheme]
  );

  const value = useMemo<ThemeContextValue>(
    () => ({ mode, setMode, effectiveTheme, cycleMode }),
    [mode, setMode, effectiveTheme, cycleMode]
  );

  return (
    <ThemeContext.Provider value={value}>
      <ThemeProvider theme={muiTheme}>{children}</ThemeProvider>
    </ThemeContext.Provider>
  );
}
