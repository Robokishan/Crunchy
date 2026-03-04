import { ArrowTopRightOnSquareIcon } from "@heroicons/react/24/solid";
import LoadingButton from "@mui/lab/LoadingButton";
import { Card, CardContent } from "@mui/material";
import { differenceInMinutes, format, formatDistance } from "date-fns";
import { useState } from "react";
import toast from "react-hot-toast";
import crunchyClient from "~/utils/crunchyClient";
import type { CompayDetail } from "~/utils/types";

interface CompanyCardProps {
  company: CompayDetail;
  onExport: (data: CompayDetail) => void;
  onCardClick?: (company: CompayDetail) => void;
}

function formatDate(value: Date | string | undefined) {
  if (!value) return "-";
  const d = typeof value === "string" ? new Date(value) : value;
  return differenceInMinutes(new Date(), d) < 60
    ? formatDistance(d, new Date(), { addSuffix: true })
    : format(d, "yyyy-MM-dd HH:mm");
}

export function CompanyCard({ company, onExport, onCardClick }: CompanyCardProps) {
  const [loading, setLoading] = useState(false);
  const [retried, setRetried] = useState<"init" | "done" | "error">("init");

  const handleRetry = () => {
    setLoading(true);
    const retryPromise = crunchyClient.post("/api/crawl/create", {
      url: [company.crunchbase_url],
    });
    toast.promise(retryPromise, {
      loading: "Pushing to queue",
      success: "Pushed to queue",
      error: "Error pushing to queue",
    });
    retryPromise
      .then(() => setRetried("done"))
      .catch(() => setRetried("error"))
      .finally(() => setLoading(false));
  };

  const industriesText = company.industries?.length
    ? company.industries.join(", ")
    : "-";
  const description = company.description?.trim() || company.long_description?.trim() || null;

  return (
    <Card
      variant="outlined"
      role={onCardClick ? "button" : undefined}
      tabIndex={onCardClick ? 0 : undefined}
      onClick={onCardClick ? () => onCardClick(company) : undefined}
      onKeyDown={
        onCardClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onCardClick(company);
              }
            }
          : undefined
      }
      className="w-full max-w-full min-w-0 overflow-hidden border-slate-200 bg-white transition-shadow hover:shadow-md dark:border-slate-600 dark:bg-slate-800/50"
      sx={{
        borderRadius: 2,
        maxWidth: "100%",
        width: "100%",
        boxSizing: "border-box",
        cursor: onCardClick ? "pointer" : undefined,
      }}
    >
      <CardContent className="p-4" sx={{ boxSizing: "border-box", "&:last-child": { pb: 2 }, maxWidth: "100%" }}>
        <div className="flex min-w-0 gap-3" style={{ minWidth: 0 }}>
          <a
            href={company.logo || "/image-broken.png"}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0"
          >
            <img
              src={company.logo || "/image-broken.png"}
              alt=""
              loading="lazy"
              width={48}
              height={48}
              className="h-12 w-12 rounded-lg object-contain bg-slate-100 dark:bg-slate-700"
            />
          </a>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              {company.website ? (
                <a
                  href={company.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-underline font-semibold text-slate-800 truncate dark:text-slate-100"
                >
                  {company.name}
                </a>
              ) : (
                <span className="font-semibold text-slate-800 truncate dark:text-slate-100">
                  {company.name}
                </span>
              )}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onExport(company);
                }}
                className="shrink-0 rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-brand-600 focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-brand-400"
                aria-label="Export to Notion"
              >
                <ArrowTopRightOnSquareIcon className="h-5 w-5" />
              </button>
            </div>
            {company.funding && (
              <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">
                {company.funding}
              </p>
            )}
            <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400" title={`Created ${formatDate(company.created_at)} · Updated ${formatDate(company.updated_at)}`}>
              C {formatDate(company.created_at)} · U {formatDate(company.updated_at)}
            </p>
            {description && (
              <p className="mt-1 line-clamp-3 text-sm text-slate-600 dark:text-slate-300" title={description}>
                {description}
              </p>
            )}
            <p className="mt-1 line-clamp-2 text-xs text-slate-500 dark:text-slate-400" title={industriesText}>
              {industriesText}
            </p>
            <LoadingButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleRetry();
              }}
              disabled={retried === "done"}
              loading={loading}
              loadingIndicator="Pushing…"
              color={
                retried === "done"
                  ? "success"
                  : retried === "error"
                    ? "error"
                    : "primary"
              }
              variant="outlined"
              sx={{ mt: 1.5, borderRadius: 2 }}
            >
              {retried === "init"
                ? "Retry crawl"
                : retried === "done"
                  ? "Pushed"
                  : "Error"}
            </LoadingButton>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
