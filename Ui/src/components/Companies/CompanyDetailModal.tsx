import { XMarkIcon } from "@heroicons/react/24/outline";
import { useMemo } from "react";
import Modal from "react-modal";
import { useThemeMode } from "~/contexts/ThemeContext";
import { useIsMobile } from "~/hooks/useIsMobile";
import type { CompayDetail } from "~/utils/types";
import {
  formatDetailValue,
  getSortedDetailEntries,
} from "./detailFields";

Modal.setAppElement("#popup");

type Props = {
  company: CompayDetail | null;
  isOpen: boolean;
  onClose: () => void;
};

export function CompanyDetailModal({ company, isOpen, onClose }: Props) {
  const { effectiveTheme } = useThemeMode();
  const isMobile = useIsMobile();
  const isDark = effectiveTheme === "dark";

  const customStyles = useMemo(
    () => ({
      content: {
        boxShadow: isDark
          ? "0 25px 50px -12px rgb(0 0 0 / 0.5), 0 0 0 1px rgb(255 255 255 / 0.06)"
          : "0 25px 50px -12px rgb(0 0 0 / 0.15), 0 0 0 1px rgb(0 0 0 / 0.05)",
        width: isMobile ? "calc(100vw - 1rem)" : "min(90vw, 640px)",
        border: "none",
        minWidth: isMobile ? 0 : "420px",
        maxWidth: isMobile ? "calc(100vw - 1rem)" : "640px",
        top: "50%",
        left: "50%",
        right: "auto",
        bottom: "auto",
        maxHeight: "calc(100vh - 4rem)",
        marginRight: "-50%",
        transform: "translate(-50%, -50%)",
        borderRadius: "16px",
        padding: isMobile ? "20px 16px 20px" : "24px 24px 24px",
        backgroundColor: isDark ? "#1e293b" : "#fff",
        color: isDark ? "#e2e8f0" : "#0f172a",
        overflowY: "auto" as const,
      } as React.CSSProperties,
      overlay: {
        zIndex: 10000,
        position: "fixed" as const,
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: isDark ? "rgba(15,23,42,0.82)" : "rgba(15,23,42,0.4)",
        backdropFilter: "blur(4px)",
      } as React.CSSProperties,
    }),
    [isDark, isMobile]
  );

  if (!company) return null;

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onClose}
      style={customStyles}
      contentLabel="Company details"
    >
      <div className="flex items-center gap-3 border-b border-slate-200 pb-3 dark:border-slate-600">
        <h2 className="text-lg font-semibold tracking-tight text-slate-800 dark:text-slate-100">
          {company.name}
        </h2>
        <button
          type="button"
          onClick={onClose}
          className="ml-auto rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-600 dark:hover:text-slate-200"
          aria-label="Close"
        >
          <XMarkIcon className="h-6 w-6" />
        </button>
      </div>
      <div className="mt-4 grid w-full grid-cols-1 gap-4 rounded-lg border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-600 dark:bg-slate-800/50 sm:grid-cols-2">
        <div className="flex h-32 w-32 items-center">
          <a
            href={company.logo || "/image-broken.png"}
            target="_blank"
            rel="noopener noreferrer"
          >
            <img
              src={company.logo || "/image-broken.png"}
              alt="company-icon"
              loading="lazy"
              width={100}
              height={100}
              className="h-[100px] w-[100px] object-contain"
            />
          </a>
        </div>
        {getSortedDetailEntries(company).map(({ key, value }, index) => (
          <div key={`${company._id}-${index}-expand`} className="flex flex-col">
            <span className="text-sm font-medium capitalize text-slate-500 dark:text-slate-400">
              {key}:
            </span>
            <span className="overflow-hidden break-words break-all text-sm text-slate-700 dark:text-slate-300">
              {formatDetailValue(value)}
            </span>
          </div>
        ))}

      </div>
    </Modal>
  );
}
