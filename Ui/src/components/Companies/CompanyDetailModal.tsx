import { XMarkIcon } from "@heroicons/react/24/outline";
import type { ReactNode } from "react";
import { useMemo } from "react";
import Modal from "react-modal";
import { useThemeMode } from "~/contexts/ThemeContext";
import { useIsMobile } from "~/hooks/useIsMobile";
import { isUrl } from "~/utils";
import type { CompayDetail } from "~/utils/types";

Modal.setAppElement("#popup");

type Props = {
  company: CompayDetail | null;
  isOpen: boolean;
  onClose: () => void;
};

function formatValue(value: unknown): ReactNode {
  if (value == null || value === "") return "-";
  if (typeof value === "string") {
    return isUrl(value) ? (
      <a href={value} target="_blank" rel="noopener noreferrer" className="link-underline">
        {value}
      </a>
    ) : (
      value
    );
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return "-";
    return value.map((item, idx, arr) =>
      typeof item === "string" && isUrl(item) ? (
        <div key={idx}>
          <a href={item} target="_blank" rel="noopener noreferrer" className="link-underline">
            {item}
          </a>
        </div>
      ) : (
        <span key={idx}>
          {String(item)}
          {arr.length - 1 !== idx && ", "}
        </span>
      )
    );
  }
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

const AFTER_LASTFUNDING = ["lastfunding", "description", "long_description"] as const;

const BELOW_UPDATED_AT = [
  "sources",
  "source_priority",
  "crunchbase_url",
  "tracxn_url",
  "match_confidence",
  "logo",
] as const;

function getDetailSortKey(
  entry: { key: string; index: number },
  foundersIndex: number,
  updatedAtIndex: number,
  createdAtIndex: number,
  longDescriptionIndex: number
): number {
  const k = entry.key;
  const i = entry.index;
  if (k === "_id") return createdAtIndex >= 0 ? createdAtIndex - 0.5 : i;
  if (k === "name") return -1;
  if (k === "website") return 0;
  if (k === "similar_companies") return 1e9;
  if (k === "founders") return foundersIndex >= 0 ? foundersIndex : i;
  if (k === "founded") return foundersIndex >= 0 ? foundersIndex + 0.5 : i;
  if (k === "lastfunding") return foundersIndex >= 0 ? foundersIndex + 1 : i;
  if (k === "normalized_domain") return longDescriptionIndex >= 0 ? longDescriptionIndex + 0.5 : i;
  if (k === "funding_usd") return longDescriptionIndex >= 0 ? longDescriptionIndex + 1 : i;
  if (k === "updated_at") return updatedAtIndex >= 0 ? updatedAtIndex : i;
  const belowIdx = BELOW_UPDATED_AT.indexOf(k as (typeof BELOW_UPDATED_AT)[number]);
  if (belowIdx !== -1)
    return updatedAtIndex >= 0 ? updatedAtIndex + 1 + belowIdx : i;
  return i;
}

function detailFieldCompare(
  a: { key: string; value: unknown; index: number },
  b: { key: string; value: unknown; index: number },
  foundersIndex: number,
  updatedAtIndex: number,
  createdAtIndex: number,
  longDescriptionIndex: number
): number {
  return (
    getDetailSortKey(a, foundersIndex, updatedAtIndex, createdAtIndex, longDescriptionIndex) -
    getDetailSortKey(b, foundersIndex, updatedAtIndex, createdAtIndex, longDescriptionIndex)
  );
}

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
        {(() => {
          const entries = Object.entries(company).map(([key, value], index) => ({
            key,
            value,
            index,
          }));
          const foundersIndex = entries.findIndex((e) => e.key === "founders");
          const updatedAtIndex = entries.findIndex((e) => e.key === "updated_at");
          const createdAtIndex = entries.findIndex((e) => e.key === "created_at");
          const longDescriptionIndex = entries.findIndex((e) => e.key === "long_description");
          return entries
            .sort((a, b) =>
              detailFieldCompare(a, b, foundersIndex, updatedAtIndex, createdAtIndex, longDescriptionIndex)
            )
            .map(({ key, value }, index) => (
          <div key={`${company._id}-${index}-expand`} className="flex flex-col">
            <span className="text-sm font-medium capitalize text-slate-500 dark:text-slate-400">
              {key}:
            </span>
            <span className="overflow-hidden break-words text-sm text-slate-700 dark:text-slate-300">
              {formatValue(value)}
            </span>
          </div>
            ));
        })()}

      </div>
    </Modal>
  );
}
