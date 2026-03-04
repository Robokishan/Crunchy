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
          background: {
            default: effectiveTheme === "dark" ? "#0f172a" : "#f8fafc",
            paper: effectiveTheme === "dark" ? "#1e293b" : "#ffffff",
          },
        },
        typography: {
          fontFamily: '"Plus Jakarta Sans", system-ui, sans-serif',
          h1: { fontWeight: 600, letterSpacing: "-0.02em" },
          h2: { fontWeight: 600, letterSpacing: "-0.02em" },
          h3: { fontWeight: 600, letterSpacing: "-0.01em" },
          body1: { lineHeight: 1.6 },
          body2: { lineHeight: 1.5 },
        },
        shape: { borderRadius: 8 },
        components: {
          MuiButton: {
            styleOverrides: {
              root: {
                textTransform: "none",
                fontWeight: 600,
                borderRadius: 8,
                "&:focus-visible": {
                  boxShadow: "0 0 0 3px rgba(37, 99, 235, 0.35)",
                },
              },
            },
          },
          MuiIconButton: {
            styleOverrides: {
              root: {
                "&:focus-visible": {
                  boxShadow: "0 0 0 3px rgba(255,255,255,0.25)",
                },
              },
            },
          },
          MuiTextField: {
            defaultProps: {
              variant: "outlined",
              size: "small",
            },
            styleOverrides: {
              root: {
                "& .MuiOutlinedInput-root": {
                  borderRadius: 8,
                  "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                    borderWidth: 2,
                  },
                },
              },
            },
          },
          MuiPaper: {
            styleOverrides: {
              root: {
                borderRadius: 12,
                backgroundImage: "none",
              },
            },
          },
          MuiSelect: {
            styleOverrides: {
              root: {
                borderRadius: 8,
              },
            },
          },
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
