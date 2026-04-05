import {
  Autocomplete,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Pagination,
  Select,
  TextField,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { type ChangeEvent, useCallback, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CompanyCard } from "~/components/Companies/CompanyCard";
import { CompanyDetailModal } from "~/components/Companies/CompanyDetailModal";
import type { Industry } from "~/hooks/industryList";
import type {
  CompayDetail,
  IndustryFundingAnalyticsResponse,
  IndustryFundingFilterState,
  IndustryFundingChartRow,
  IndustryQueryGroup,
  IndustryQueryGroupPayload,
} from "~/utils/types";
import crunchyClient from "~/utils/crunchyClient";

type CompanyApiResponse = {
  results: CompayDetail[];
  count: number;
};

type CompanySortField = "created_at" | "funding_usd";

type CompanySortState = {
  id: CompanySortField;
  desc: boolean;
};

const DEFAULT_SORTING: CompanySortState = { id: "created_at", desc: true };
const COMPANY_PAGE_SIZE = 100;

function createIndustryGroup(overrides?: Partial<IndustryQueryGroup>): IndustryQueryGroup {
  return {
    id:
      overrides?.id ??
      `group-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
    operator: overrides?.operator ?? "any",
    industries: overrides?.industries ?? [],
  };
}

function parseNumber(value: string | null): number | undefined {
  if (value == null || value.trim() === "") return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

function formatCurrency(value: number | undefined) {
  if (value == null || !Number.isFinite(value)) return "-";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function normalizeGroupIndustries(industries: string[]) {
  return Array.from(
    new Set(
      industries
        .map((industry) => industry.trim())
        .filter(Boolean)
    )
  );
}

function toIndustryGroupPayloads(
  groups: IndustryQueryGroup[]
): IndustryQueryGroupPayload[] {
  return groups
    .map((group) => ({
      operator: group.operator === "all" ? "all" : "any",
      industries: normalizeGroupIndustries(group.industries),
    }))
    .filter((group) => group.industries.length > 0);
}

function parseIndustryGroups(searchParams: URLSearchParams) {
  const rawGroups = searchParams.get("industryGroups");
  if (!rawGroups) return [createIndustryGroup()];

  try {
    const parsed = JSON.parse(rawGroups);
    if (!Array.isArray(parsed)) return [createIndustryGroup()];
    const groups = parsed
      .filter((group): group is IndustryQueryGroupPayload =>
        Boolean(group) && typeof group === "object" && Array.isArray(group.industries)
      )
      .map((group) =>
        createIndustryGroup({
          operator: group.operator === "all" ? "all" : "any",
          industries: normalizeGroupIndustries(group.industries),
        })
      );
    return groups.length > 0 ? groups : [createIndustryGroup()];
  } catch {
    return [createIndustryGroup()];
  }
}

function parseFilters(searchParams: URLSearchParams): IndustryFundingFilterState {
  return {
    search: searchParams.get("search") ?? "",
    fundingMin: parseNumber(searchParams.get("fundingMin")),
    fundingMax: parseNumber(searchParams.get("fundingMax")),
    industryGroupOperator:
      searchParams.get("industryGroupOperator") === "all" ? "all" : "any",
    industryGroups: parseIndustryGroups(searchParams),
  };
}

function parseSorting(searchParams: URLSearchParams): CompanySortState {
  const rawSort = searchParams.get("companySort");
  if (!rawSort) return DEFAULT_SORTING;
  const [id, direction] = rawSort.split(":");
  if ((id === "created_at" || id === "funding_usd") && (direction === "asc" || direction === "desc")) {
    return {
      id,
      desc: direction === "desc",
    };
  }
  return DEFAULT_SORTING;
}

function parsePage(searchParams: URLSearchParams): number {
  const rawPage = Number(searchParams.get("companyPage"));
  if (Number.isInteger(rawPage) && rawPage > 0) return rawPage;
  return 1;
}

function buildSearchParams(
  filters: IndustryFundingFilterState,
  selectedIndustry: string | null,
  sorting: CompanySortState,
  page: number
) {
  const params = new URLSearchParams();
  if (filters.search.trim()) params.set("search", filters.search.trim());
  if (filters.fundingMin != null) params.set("fundingMin", String(filters.fundingMin));
  if (filters.fundingMax != null) params.set("fundingMax", String(filters.fundingMax));
  params.set("industryGroupOperator", filters.industryGroupOperator);
  const payloadGroups = toIndustryGroupPayloads(filters.industryGroups);
  if (payloadGroups.length > 0) {
    params.set("industryGroups", JSON.stringify(payloadGroups));
  }
  params.set("companySort", `${sorting.id}:${sorting.desc ? "desc" : "asc"}`);
  params.set("companyPage", String(page));
  if (selectedIndustry) params.set("selectedIndustry", selectedIndustry);
  return params;
}

function buildCompanyFilters(
  filters: IndustryFundingFilterState,
  selectedIndustry: string | null
) {
  const payloadGroups = toIndustryGroupPayloads(filters.industryGroups);
  const queryFilters: Array<{
    id: string;
    value?: unknown;
    operator?: "any" | "all";
    groups?: IndustryQueryGroupPayload[];
  }> = [];

  if (filters.search.trim()) queryFilters.push({ id: "name", value: filters.search.trim() });
  if (payloadGroups.length > 0) {
    queryFilters.push({
      id: "industry_groups",
      groups: payloadGroups,
      operator: filters.industryGroupOperator,
    });
  }
  if (selectedIndustry) {
    queryFilters.push({
      id: "industries",
      value: [selectedIndustry],
      operator: "all",
    });
  }
  if (filters.fundingMin != null || filters.fundingMax != null) {
    queryFilters.push({
      id: "funding_usd",
      value: [filters.fundingMin ?? undefined, filters.fundingMax ?? undefined],
    });
  }
  return queryFilters;
}

function buildChartParams(filters: IndustryFundingFilterState) {
  return {
    search: filters.search.trim() || undefined,
    fundingMin: filters.fundingMin,
    fundingMax: filters.fundingMax,
    industryGroupOperator: filters.industryGroupOperator,
    industryGroups: JSON.stringify(toIndustryGroupPayloads(filters.industryGroups)),
  };
}

function buildQueryPreview(filters: IndustryFundingFilterState) {
  const groups = toIndustryGroupPayloads(filters.industryGroups);
  if (groups.length === 0) return "No base industry conditions.";

  return groups
    .map((group) => {
      const joiner = group.operator === "all" ? " AND " : " OR ";
      const items = group.industries.map((industry) => `"${industry}"`).join(joiner);
      return group.industries.length > 1 ? `( ${items} )` : items;
    })
    .join(filters.industryGroupOperator === "all" ? " AND " : " OR ");
}

function sortLabel(sorting: CompanySortState) {
  const direction = sorting.desc ? "desc" : "asc";
  const fieldLabel = sorting.id === "funding_usd" ? "funding" : "created_at";
  return `${fieldLabel} ${direction}`;
}

function nextSortState(current: CompanySortState, field: CompanySortField): CompanySortState {
  if (current.id === field) {
    return {
      id: field,
      desc: !current.desc,
    };
  }
  return {
    id: field,
    desc: true,
  };
}

function sortArrow(sorting: CompanySortState, field: CompanySortField) {
  if (sorting.id !== field) return "↕";
  return sorting.desc ? "↓" : "↑";
}

function IndustryBars({
  rows,
  selectedIndustry,
  onSelect,
}: {
  rows: IndustryFundingChartRow[];
  selectedIndustry: string | null;
  onSelect: (industry: string) => void;
}) {
  const maxFunding = rows.reduce((max, row) => Math.max(max, row.median_funding_usd), 0);

  if (rows.length === 0) {
    return (
      <div className="rounded-card border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-slate-600 dark:text-slate-400">
        No industries match the current filters.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {rows.map((row) => {
        const ratio = maxFunding > 0 ? (row.median_funding_usd / maxFunding) * 100 : 0;
        const isSelected = row.industry === selectedIndustry;
        return (
          <button
            key={row.industry}
            type="button"
            onClick={() => onSelect(row.industry)}
            className={`group flex w-full items-center gap-3 rounded-card border px-4 py-3 text-left transition ${
              isSelected
                ? "border-brand-500 bg-brand-50 dark:border-brand-400 dark:bg-brand-500/10"
                : "border-slate-200 bg-white hover:border-brand-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800/40 dark:hover:border-brand-500/60 dark:hover:bg-slate-800"
            }`}
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">
                    {row.industry}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {row.company_count} companies
                  </p>
                </div>
                <span className="shrink-0 text-sm font-medium text-slate-700 dark:text-slate-200">
                  {formatCurrency(row.median_funding_usd)}
                </span>
              </div>
              <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
                <div
                  className={`h-full rounded-full transition-all ${
                    isSelected
                      ? "bg-gradient-to-r from-brand-500 to-brand-700 dark:from-brand-400 dark:to-cyan-300"
                      : "bg-gradient-to-r from-sky-500 to-blue-700 dark:from-sky-400 dark:to-blue-300"
                  }`}
                  style={{ width: `${Math.max(ratio, 4)}%` }}
                />
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

export function IndustryFundingAnalytics({
  industries,
}: {
  industries: Industry[];
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState<IndustryFundingFilterState>(() =>
    parseFilters(searchParams)
  );
  const [selectedIndustry, setSelectedIndustry] = useState<string | null>(
    () => searchParams.get("selectedIndustry") ?? null
  );
  const [sorting, setSorting] = useState<CompanySortState>(() =>
    parseSorting(searchParams)
  );
  const [companyPage, setCompanyPage] = useState<number>(() =>
    parsePage(searchParams)
  );
  const [draftSearch, setDraftSearch] = useState(filters.search);
  const [detailCompany, setDetailCompany] = useState<CompayDetail | null>(null);

  const syncUrl = useCallback(
    (
      nextFilters: IndustryFundingFilterState,
      nextSelectedIndustry: string | null,
      nextSorting: CompanySortState,
      nextPage: number
    ) => {
      setSearchParams(buildSearchParams(nextFilters, nextSelectedIndustry, nextSorting, nextPage), {
        replace: true,
      });
    },
    [setSearchParams]
  );

  const applyFilters = useCallback(() => {
    const nextFilters = {
      ...filters,
      search: draftSearch,
    };
    setFilters(nextFilters);
    setCompanyPage(1);
    syncUrl(nextFilters, selectedIndustry, sorting, 1);
  }, [draftSearch, filters, selectedIndustry, sorting, syncUrl]);

  const resetFilters = useCallback(() => {
    const nextFilters: IndustryFundingFilterState = {
      search: "",
      fundingMin: undefined,
      fundingMax: undefined,
      industryGroupOperator: "any",
      industryGroups: [createIndustryGroup()],
    };
    setDraftSearch("");
    setSelectedIndustry(null);
    setSorting(DEFAULT_SORTING);
    setCompanyPage(1);
    setFilters(nextFilters);
    syncUrl(nextFilters, null, DEFAULT_SORTING, 1);
  }, [syncUrl]);

  const updateFilters = useCallback(
    (
      updater: (current: IndustryFundingFilterState) => IndustryFundingFilterState,
      nextSelectedIndustry = selectedIndustry,
      nextSorting = sorting,
      nextPage = 1
    ) => {
      setFilters((current) => {
        const nextFilters = updater(current);
        syncUrl(nextFilters, nextSelectedIndustry, nextSorting, nextPage);
        return nextFilters;
      });
      setCompanyPage(nextPage);
    },
    [selectedIndustry, sorting, syncUrl]
  );

  const handleIndustrySelection = useCallback(
    (industry: string) => {
      const nextSelected = selectedIndustry === industry ? null : industry;
      setSelectedIndustry(nextSelected);
      setCompanyPage(1);
      syncUrl(filters, nextSelected, sorting, 1);
    },
    [filters, selectedIndustry, sorting, syncUrl]
  );

  const handleSortChange = useCallback(
    (field: CompanySortField) => {
      const nextSorting = nextSortState(sorting, field);
      setSorting(nextSorting);
      setCompanyPage(1);
      syncUrl(filters, selectedIndustry, nextSorting, 1);
    },
    [filters, selectedIndustry, sorting, syncUrl]
  );

  const handlePageChange = useCallback(
    (_event: ChangeEvent<unknown>, nextPage: number) => {
      setCompanyPage(nextPage);
      syncUrl(filters, selectedIndustry, sorting, nextPage);
    },
    [filters, selectedIndustry, sorting, syncUrl]
  );

  const industryOptions = useMemo(
    () => industries.map((industry) => industry.industry).sort((a, b) => a.localeCompare(b)),
    [industries]
  );

  const queryPreview = useMemo(() => buildQueryPreview(filters), [filters]);

  const chartQuery = useQuery({
    queryKey: ["industry-funding-chart", filters],
    queryFn: async () => {
      const { data } = await crunchyClient.get<IndustryFundingAnalyticsResponse>(
        "/public/analytics/industry-funding",
        {
          params: buildChartParams(filters),
        }
      );
      return data;
    },
  });

  const companyQuery = useQuery({
    queryKey: ["industry-funding-companies", filters, selectedIndustry, sorting, companyPage],
    queryFn: async () => {
      const { data } = await crunchyClient.get<CompanyApiResponse>("/public/comp", {
        params: {
          filters: JSON.stringify(buildCompanyFilters(filters, selectedIndustry)),
          sorting: JSON.stringify([sorting]),
          page: companyPage,
        },
      });
      return data;
    },
  });

  const chartRows = chartQuery.data?.results ?? [];
  const companies = companyQuery.data?.results ?? [];
  const totalCompanyCount = companyQuery.data?.count ?? 0;
  const totalCompanyPages = Math.max(1, Math.ceil(totalCompanyCount / COMPANY_PAGE_SIZE));

  return (
    <div className="mx-auto my-4 flex w-full max-w-7xl flex-col gap-6">
      <section className="card-base">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="page-title">Industry Funding Analytics</h1>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Median funding by industry from MongoDB using the existing{" "}
              <code>funding_usd</code> field.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" className="btn-secondary" onClick={applyFilters}>
              Apply filters
            </button>
            <button type="button" className="btn-secondary" onClick={resetFilters}>
              Reset
            </button>
          </div>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(220px,1fr)_minmax(220px,1fr)]">
          <TextField
            label="Search companies"
            value={draftSearch}
            onChange={(event) => setDraftSearch(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") applyFilters();
            }}
            fullWidth
          />
          <TextField
            label="Funding min (USD)"
            type="number"
            value={filters.fundingMin ?? ""}
            onChange={(event) => {
              const nextValue = parseNumber(event.target.value) ?? undefined;
              updateFilters((current) => ({
                ...current,
                fundingMin: nextValue,
              }));
            }}
            fullWidth
          />
          <TextField
            label="Funding max (USD)"
            type="number"
            value={filters.fundingMax ?? ""}
            onChange={(event) => {
              const nextValue = parseNumber(event.target.value) ?? undefined;
              updateFilters((current) => ({
                ...current,
                fundingMax: nextValue,
              }));
            }}
            fullWidth
          />
        </div>

        <div className="mt-5 rounded-card border border-slate-200/80 p-4 dark:border-slate-700/70">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                Industry Query Builder
              </p>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                Build grouped logic like <code>(AI OR ML) AND (Software OR SaaS)</code>.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500 dark:text-slate-400">Combine groups with</span>
              <FormControl size="small" sx={{ minWidth: 180 }}>
                <Select
                  value={filters.industryGroupOperator}
                  onChange={(event) => {
                    const nextOperator = event.target.value as "any" | "all";
                    updateFilters((current) => ({
                      ...current,
                      industryGroupOperator: nextOperator,
                    }));
                  }}
                >
                  <MenuItem value="any">OR between groups</MenuItem>
                  <MenuItem value="all">AND between groups</MenuItem>
                </Select>
              </FormControl>
            </div>
          </div>

          <div className="mt-4 space-y-4">
            {filters.industryGroups.map((group, index) => (
              <div
                key={group.id}
                className="rounded-card border border-slate-200 bg-slate-50/60 p-4 dark:border-slate-700 dark:bg-slate-800/50"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="text-sm font-medium text-slate-700 dark:text-slate-200">
                    Group {index + 1}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <FormControl size="small" sx={{ minWidth: 180 }}>
                      <InputLabel id={`group-operator-${group.id}`}>Inside group</InputLabel>
                      <Select
                        labelId={`group-operator-${group.id}`}
                        label="Inside group"
                        value={group.operator}
                        onChange={(event) => {
                          const nextOperator = event.target.value as "any" | "all";
                          updateFilters((current) => ({
                            ...current,
                            industryGroups: current.industryGroups.map((item) =>
                              item.id === group.id
                                ? { ...item, operator: nextOperator }
                                : item
                            ),
                          }));
                        }}
                      >
                        <MenuItem value="any">OR inside group</MenuItem>
                        <MenuItem value="all">AND inside group</MenuItem>
                      </Select>
                    </FormControl>
                    {filters.industryGroups.length > 1 ? (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => {
                          updateFilters((current) => {
                            const nextGroups = current.industryGroups.filter(
                              (item) => item.id !== group.id
                            );
                            return {
                              ...current,
                              industryGroups:
                                nextGroups.length > 0 ? nextGroups : [createIndustryGroup()],
                            };
                          });
                        }}
                      >
                        Remove group
                      </button>
                    ) : null}
                  </div>
                </div>

                <div className="mt-3">
                  <Autocomplete
                    multiple
                    options={industryOptions}
                    value={group.industries}
                    onChange={(_, value) => {
                      const nextIndustries = normalizeGroupIndustries(value);
                      updateFilters((current) => ({
                        ...current,
                        industryGroups: current.industryGroups.map((item) =>
                          item.id === group.id
                            ? { ...item, industries: nextIndustries }
                            : item
                        ),
                      }));
                    }}
                    renderTags={(value, getTagProps) =>
                      value.map((option, chipIndex) => (
                        <Chip
                          variant="outlined"
                          label={option}
                          {...getTagProps({ index: chipIndex })}
                          key={`${group.id}-${option}`}
                        />
                      ))
                    }
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label={`Industries in group ${index + 1}`}
                        placeholder="Select industries"
                      />
                    )}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                updateFilters((current) => ({
                  ...current,
                  industryGroups: [...current.industryGroups, createIndustryGroup()],
                }));
              }}
            >
              Add group
            </button>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Empty groups are ignored until you add industries.
            </p>
          </div>

          <div className="mt-4 rounded-card border border-dashed border-slate-300 p-4 dark:border-slate-600">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Query Preview
            </p>
            <p className="mt-2 break-words font-mono text-sm text-slate-700 dark:text-slate-200">
              {queryPreview}
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <span>Chart metric: median funding_usd</span>
          {selectedIndustry ? (
            <Chip
              color="primary"
              variant="outlined"
              label={`Drilldown: ${selectedIndustry}`}
              onDelete={() => handleIndustrySelection(selectedIndustry)}
            />
          ) : null}
          {selectedIndustry ? (
            <span>Clicked chart industry is applied as an extra drilldown condition.</span>
          ) : null}
        </div>
      </section>

      <section className="card-base">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="page-title">Industry Distribution</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Click a bar to filter the company table below.
            </p>
          </div>
          {chartQuery.isFetching ? <CircularProgress size={24} /> : null}
        </div>
        <div className="mt-5 max-h-[42rem] overflow-y-auto pr-1">
          <IndustryBars
            rows={chartRows}
            selectedIndustry={selectedIndustry}
            onSelect={handleIndustrySelection}
          />
        </div>
      </section>

      <section className="card-base">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="page-title">Companies</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Page {companyPage} of {totalCompanyPages} · sorted by <code>{sortLabel(sorting)}</code>. Results update with the analytics filters and chart drilldown.
            </p>
          </div>
          {companyQuery.isFetching ? <CircularProgress size={24} /> : null}
        </div>

        <div className="mt-4 hidden overflow-hidden rounded-card border border-slate-200 dark:border-slate-700 lg:block">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead className="bg-slate-50 dark:bg-slate-800/70">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Company</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 text-left transition-colors hover:text-slate-700 dark:hover:text-slate-200"
                      onClick={() => handleSortChange("funding_usd")}
                    >
                      <span>Funding</span>
                      <span aria-hidden>{sortArrow(sorting, "funding_usd")}</span>
                    </button>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Industries</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 text-left transition-colors hover:text-slate-700 dark:hover:text-slate-200"
                      onClick={() => handleSortChange("created_at")}
                    >
                      <span>Created</span>
                      <span aria-hidden>{sortArrow(sorting, "created_at")}</span>
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-700 dark:bg-slate-900/20">
                {companies.map((company) => (
                  <tr
                    key={company._id}
                    className="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/60"
                    onClick={() => setDetailCompany(company)}
                  >
                    <td className="px-4 py-3">
                      <div className="min-w-0">
                        <p className="truncate font-medium text-slate-800 dark:text-slate-100">{company.name}</p>
                        <p className="truncate text-xs text-slate-500 dark:text-slate-400">{company.website || "-"}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-200">
                      {formatCurrency(company.funding_usd)}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-300">
                      {(company.industries ?? []).join(", ") || "-"}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-300">
                      {company.created_at ? new Date(company.created_at).toLocaleDateString() : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-4 grid gap-3 lg:hidden">
          <div className="flex justify-end">
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel id="company-sort-label">Company sort</InputLabel>
              <Select
                labelId="company-sort-label"
                label="Company sort"
                value={`${sorting.id}:${sorting.desc ? "desc" : "asc"}`}
                onChange={(event) => {
                  const [field, direction] = String(event.target.value).split(":");
                  if (
                    (field === "created_at" || field === "funding_usd") &&
                    (direction === "asc" || direction === "desc")
                  ) {
                    const nextSorting: CompanySortState = {
                      id: field,
                      desc: direction === "desc",
                    };
                    setSorting(nextSorting);
                    setCompanyPage(1);
                    syncUrl(filters, selectedIndustry, nextSorting, 1);
                  }
                }}
              >
                <MenuItem value="created_at:desc">Created desc</MenuItem>
                <MenuItem value="created_at:asc">Created asc</MenuItem>
                <MenuItem value="funding_usd:desc">Funding desc</MenuItem>
                <MenuItem value="funding_usd:asc">Funding asc</MenuItem>
              </Select>
            </FormControl>
          </div>
          {companies.map((company) => (
            <CompanyCard
              key={company._id}
              company={company}
              onExport={() => undefined}
              onCardClick={setDetailCompany}
            />
          ))}
        </div>

        {totalCompanyCount > COMPANY_PAGE_SIZE ? (
          <div className="mt-5 flex justify-center">
            <Pagination
              count={totalCompanyPages}
              page={companyPage}
              onChange={handlePageChange}
              color="primary"
              showFirstButton
              showLastButton
              siblingCount={1}
              boundaryCount={1}
            />
          </div>
        ) : null}

        {!companyQuery.isFetching && companies.length === 0 ? (
          <div className="mt-4 rounded-card border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-slate-600 dark:text-slate-400">
            No companies match the current analytics filters.
          </div>
        ) : null}
      </section>

      <CompanyDetailModal
        company={detailCompany}
        isOpen={detailCompany != null}
        onClose={() => setDetailCompany(null)}
      />
    </div>
  );
}
