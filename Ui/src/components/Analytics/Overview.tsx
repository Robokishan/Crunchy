import {
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import type {
  IndustryOverviewAnalyticsResponse,
  IndustryOverviewCountRow,
  IndustryOverviewFundingRow,
} from "~/utils/types";
import crunchyClient from "~/utils/crunchyClient";
import { FundingBracketDistribution } from "./FundingBracketDistribution";
import { AnalyticsNav } from "./Nav";

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatCompactCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function parseTopN(searchParams: URLSearchParams) {
  const rawValue = Number(searchParams.get("topN"));
  if ([25, 50, 100].includes(rawValue)) return rawValue;
  return 50;
}

function OverviewBars({
  title,
  subtitle,
  rows,
  valueFor,
  labelFor,
  titleFor,
}: {
  title: string;
  subtitle: string;
  rows: IndustryOverviewCountRow[] | IndustryOverviewFundingRow[];
  valueFor: (row: IndustryOverviewCountRow | IndustryOverviewFundingRow) => number;
  labelFor: (row: IndustryOverviewCountRow | IndustryOverviewFundingRow) => string;
  titleFor?: (row: IndustryOverviewCountRow | IndustryOverviewFundingRow) => string;
}) {
  const maxValue = rows.reduce((max, row) => Math.max(max, valueFor(row)), 0);

  return (
    <section className="card-base">
      <div>
        <h2 className="page-title">{title}</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{subtitle}</p>
      </div>
      <div className="mt-5 space-y-3">
        {rows.length === 0 ? (
          <div className="rounded-card border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-slate-600 dark:text-slate-400">
            No data available.
          </div>
        ) : (
          rows.map((row) => {
            const value = valueFor(row);
            const ratio = maxValue > 0 ? (value / maxValue) * 100 : 0;
            return (
              <div
                key={row.industry}
                className="rounded-card border border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-800/40"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">
                      {row.industry}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {row.company_count} companies
                    </p>
                  </div>
                  <span
                    className="shrink-0 text-sm font-medium text-slate-700 dark:text-slate-200"
                    title={titleFor?.(row) ?? labelFor(row)}
                  >
                    {labelFor(row)}
                  </span>
                </div>
                <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-400"
                    style={{ width: `${Math.max(ratio, 4)}%` }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

export function IndustryOverviewAnalytics() {
  const [searchParams, setSearchParams] = useSearchParams();
  const topN = useMemo(() => parseTopN(searchParams), [searchParams]);

  const updateTopN = useCallback(
    (nextTopN: number) => {
      const nextParams = new URLSearchParams(searchParams);
      nextParams.set("topN", String(nextTopN));
      setSearchParams(nextParams, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  const overviewQuery = useQuery({
    queryKey: ["industry-overview", topN],
    queryFn: async () => {
      const { data } = await crunchyClient.get<IndustryOverviewAnalyticsResponse>(
        "/public/analytics/industry-overview",
        { params: { topN } }
      );
      return data;
    },
    placeholderData: (previousData) => previousData,
  });

  const data = overviewQuery.data;

  return (
    <div className="mx-auto my-4 flex w-full max-w-7xl flex-col gap-6">
      <section className="card-base">
        <AnalyticsNav />
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="page-title">Database Overview</h1>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Bird&apos;s-eye distribution of the entire database across industries, company count, and total funding.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {overviewQuery.isFetching ? <CircularProgress size={22} /> : null}
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel id="overview-topn-label">Show top</InputLabel>
              <Select
                labelId="overview-topn-label"
                label="Show top"
                value={String(topN)}
                onChange={(event) => updateTopN(Number(event.target.value))}
              >
                <MenuItem value="25">Top 25</MenuItem>
                <MenuItem value="50">Top 50</MenuItem>
                <MenuItem value="100">Top 100</MenuItem>
              </Select>
            </FormControl>
          </div>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-card border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800/40">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Total companies</p>
            <p className="mt-2 text-2xl font-semibold text-slate-800 dark:text-slate-100">
              {data?.summary.total_companies ?? "-"}
            </p>
          </div>
          <div className="rounded-card border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800/40">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Funded companies</p>
            <p className="mt-2 text-2xl font-semibold text-slate-800 dark:text-slate-100">
              {data?.summary.funded_companies ?? "-"}
            </p>
          </div>
          <div className="rounded-card border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800/40">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Total industries</p>
            <p className="mt-2 text-2xl font-semibold text-slate-800 dark:text-slate-100">
              {data?.summary.total_industries ?? "-"}
            </p>
          </div>
          <div className="rounded-card border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800/40">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Total funding</p>
            <p
              className="mt-2 text-2xl font-semibold text-slate-800 dark:text-slate-100"
              title={data ? formatCurrency(data.summary.total_funding_usd) : undefined}
            >
              {data ? formatCompactCurrency(data.summary.total_funding_usd) : "-"}
            </p>
          </div>
        </div>
      </section>

      <FundingBracketDistribution />

      <div className="grid gap-6 xl:grid-cols-2">
        <OverviewBars
          title="Industry By Company Count"
          subtitle="Whole-database distribution by number of companies tagged to each industry."
          rows={data?.industry_by_company_count ?? []}
          valueFor={(row) => row.company_count}
          labelFor={(row) => `${row.company_count}`}
        />
        <OverviewBars
          title="Industry By Total Funding"
          subtitle="Whole-database distribution by summed funding_usd across companies in each industry."
          rows={data?.industry_by_total_funding ?? []}
          valueFor={(row) => row.total_funding_usd}
          labelFor={(row) => formatCompactCurrency(row.total_funding_usd)}
          titleFor={(row) => formatCurrency(row.total_funding_usd)}
        />
      </div>
    </div>
  );
}
