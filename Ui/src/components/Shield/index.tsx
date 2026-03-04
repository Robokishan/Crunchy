import React from "react";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { Toaster } from "react-hot-toast";
import { ToastContainer } from "react-toastify";
import type { CloseButtonProps } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useThemeMode } from "~/contexts/ThemeContext";
import "~/styles/toast.css";

function ToastCloseButton({ closeToast, theme }: CloseButtonProps) {
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      onClick={closeToast}
      aria-label="Close notification"
      className="crunchy-toast-close-btn"
      data-dark={isDark ? "" : undefined}
    >
      <XMarkIcon className="h-5 w-5" strokeWidth={2} />
    </button>
  );
}

interface Props {
  children: JSX.Element | React.ReactNode;
}

export default function Shield({ children }: Props) {
  const { effectiveTheme } = useThemeMode();
  const [queryClient] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <Toaster
        position="top-right"
        gutter={12}
        containerClassName="crunchy-toaster"
        toastOptions={{
          duration: 4000,
          className: "crunchy-toast",
          success: {
            iconTheme: { primary: "#10b981", secondary: "#fff" },
            className: "crunchy-toast crunchy-toast-success",
          },
          error: {
            iconTheme: { primary: "#ef4444", secondary: "#fff" },
            className: "crunchy-toast crunchy-toast-error",
          },
          loading: {
            iconTheme: { primary: "#2563eb", secondary: "#e2e8f0" },
            className: "crunchy-toast crunchy-toast-loading",
          },
        }}
      />
      <ToastContainer
        position="top-right"
        hideProgressBar
        newestOnTop
        theme={effectiveTheme === "dark" ? "dark" : "light"}
        className="crunchy-toastify-container"
        toastClassName="crunchy-toastify-toast"
        bodyClassName="crunchy-toastify-body"
        closeButton={ToastCloseButton}
      />
      {children}
    </QueryClientProvider>
  );
}
