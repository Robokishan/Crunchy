import { ArrowTopRightOnSquareIcon } from "@heroicons/react/24/solid";
import LoadingButton from "@mui/lab/LoadingButton";
import {
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import { useInfiniteQuery } from "@tanstack/react-query";
import { differenceInMinutes, format, formatDistance } from "date-fns";
import {
  MaterialReactTable,
  type MRT_ColumnDef,
  MRT_ColumnFiltersState,
  type MRT_ExpandedState,
  type MRT_RowVirtualizer,
  MRT_SortingState,
  useMaterialReactTable,
} from "material-react-table";
import {
  type UIEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import { isUrl } from "~/utils";
import crunchyClient from "~/utils/crunchyClient";
import {
  detailKeyToLabel,
  formatDetailValue,
  getSortedDetailEntries,
  getSortedDetailEntriesForMobile,
  isMetadataDetailKey,
} from "./detailFields";
import { type CompayDetail } from "~/utils/types";
import { getBaseURL } from "../../utils/baseUrl";
import CreateCrawl from "../CreateCrawl";
import ExportToNotion from "../ExportNotionModal";
import { Pending } from "../Pending";
import useIndustryList, { Industry } from "~/hooks/industryList";
import { useIsMobile } from "~/hooks/useIsMobile";
import { useHeaderScroll } from "~/contexts/HeaderScrollContext";
import { CompanyCard } from "./CompanyCard";
import { CompanyDetailModal } from "./CompanyDetailModal";
import { MobileFilters } from "./MobileFilters";

type UserApiResponse = {
  results: Array<CompayDetail>;
  count: number;
  next?: string;
  previous?: string;
};

type IndustryOptionSortBy = "industryCount" | "alphabetical" | "default";

const DEFAULT_SORTING: MRT_SortingState = [{ id: "created_at", desc: true }];

function parseTableStateFromSearchParams(
  params: URLSearchParams
): {
  columnFilters: MRT_ColumnFiltersState;
  globalFilter: string | undefined;
  sorting: MRT_SortingState;
} {
  const searchQ = params.get("search") ?? params.get("q") ?? "";
  const globalFilter = searchQ.trim() || undefined;

  const sortParam = params.get("sort");
  let sorting: MRT_SortingState = DEFAULT_SORTING;
  if (sortParam) {
    const [id, dir] = sortParam.split(":");
    if (id && (dir === "asc" || dir === "desc"))
      sorting = [{ id, desc: dir === "desc" }];
  }

  const industriesParam = params.get("industries");
  const industryList = industriesParam
    ? industriesParam.split(",").map((s) => s.trim()).filter(Boolean)
    : [];
  const fundingMin = params.get("fundingMin");
  const fundingMax = params.get("fundingMax");
  const minNum =
    fundingMin != null && fundingMin !== "" ? Number(fundingMin) : undefined;
  const maxNum =
    fundingMax != null && fundingMax !== "" ? Number(fundingMax) : undefined;

  const columnFilters: MRT_ColumnFiltersState = [];
  if (industryList.length > 0)
    columnFilters.push({ id: "industries", value: industryList });
  if (minNum != null || maxNum != null)
    columnFilters.push({
      id: "funding_usd",
      value: [minNum ?? undefined, maxNum ?? undefined],
    });

  return { columnFilters, globalFilter, sorting };
}

function buildSearchParamsFromState(
  columnFilters: MRT_ColumnFiltersState,
  globalFilter: string | undefined,
  sorting: MRT_SortingState
): URLSearchParams {
  const params = new URLSearchParams();
  if (globalFilter?.trim()) params.set("search", globalFilter.trim());
  const sort = sorting[0];
  if (sort) params.set("sort", `${sort.id}:${sort.desc ? "desc" : "asc"}`);
  const industries = columnFilters.find((f) => f.id === "industries")
    ?.value as string[] | undefined;
  if (industries?.length) params.set("industries", industries.join(","));
  const funding = columnFilters.find((f) => f.id === "funding_usd")
    ?.value as [number | undefined, number | undefined] | undefined;
  if (funding) {
    if (funding[0] != null) params.set("fundingMin", String(funding[0]));
    if (funding[1] != null) params.set("fundingMax", String(funding[1]));
  }
  return params;
}

export const CompanyDetails = ({ industries }: { industries: Industry[] }) => {
  const isMobile = useIsMobile();
  const [searchParams, setSearchParams] = useSearchParams();
  const { setHeaderHidden, scrollContainerRef } = useHeaderScroll();
  const tableContainerRef = useRef<HTMLDivElement>(null); //we can get access to the underlying TableContainer element and react to its scroll events
  const mobileCardsContainerRef = useRef<HTMLDivElement>(null);
  const touchStartYRef = useRef<number>(0);
  const rowVirtualizerInstanceRef =
    useRef<MRT_RowVirtualizer<HTMLDivElement, HTMLTableRowElement>>(null);
  const [modalIsOpen, setModal] = useState(false);
  const [crawlModalIsOpen, setOpenCrawlModal] = useState(false);
  const [modalData, setModalData] = useState();
  const [detailModalCompany, setDetailModalCompany] = useState<CompayDetail | null>(null);

  const [columnFilters, setColumnFilters] = useState<MRT_ColumnFiltersState>(
    () => parseTableStateFromSearchParams(searchParams).columnFilters
  );
  const [globalFilter, setGlobalFilter] = useState<string | undefined>(
    () => parseTableStateFromSearchParams(searchParams).globalFilter
  );
  const [sorting, setSorting] = useState<MRT_SortingState>(
    () => parseTableStateFromSearchParams(searchParams).sorting
  );
  const [industryOptionSortBy, setIndustryOptionSortBy] =
    useState<IndustryOptionSortBy>("default");
  const [expanded, setExpanded] = useState<MRT_ExpandedState>({});
  const [tableContainerHeight, setTableContainerHeight] =
    useState<string>("80vh");

  const selectedIndustry = useMemo(
    () => columnFilters.find((f) => f.id === "industries")?.value as string[],
    [columnFilters]
  );

  const fundingUsdRange = useMemo(() => {
    const v = columnFilters.find((f) => f.id === "funding_usd")?.value;
    if (Array.isArray(v) && v.length >= 2) return [v[0] as number | undefined, v[1] as number | undefined] as const;
    return [undefined, undefined] as const;
  }, [columnFilters]);

  const setFundingUsdFilter = useCallback((min: number | undefined, max: number | undefined) => {
    setColumnFilters((prev) => {
      const rest = prev.filter((f) => f.id !== "funding_usd");
      if (min == null && max == null) return rest;
      return [...rest, { id: "funding_usd", value: [min ?? undefined, max ?? undefined] }];
    });
  }, []);

  const filterIndustry = useIndustryList(
    industries,
    selectedIndustry,
    industryOptionSortBy
  );

  const { data, fetchNextPage, isError, isFetching, isLoading } =
    useInfiniteQuery<UserApiResponse>({
      queryKey: ["table-data", columnFilters, globalFilter, sorting],
      queryFn: async ({ pageParam = 1 }) => {
        const url = new URL("/public/comp", getBaseURL());
        url.searchParams.set("page", `${pageParam}`);
        url.searchParams.set("filters", JSON.stringify(columnFilters ?? []));
        url.searchParams.set("search", (globalFilter as string) ?? null);
        url.searchParams.set("sorting", JSON.stringify(sorting ?? []));
        const { data } = await crunchyClient.get<UserApiResponse>(
          url.toString()
        );
        return data;
      },
      initialPageParam: 1,
      getNextPageParam: (_lastGroup, groups) => {
        return !!_lastGroup.next ? groups.length + 1 : undefined;
      },
      refetchOnWindowFocus: false,
    });

  const openExportModal = useCallback(
    (_data: any) => {
      setModalData(_data);
      setModal(true);
    },
    [modalIsOpen]
  );

  const flatData = useMemo(
    () => data?.pages.flatMap((page) => page.results) ?? [],
    [data]
  );

  const totalDBRowCount = data?.pages[0]?.count ?? 0;
  const totalFetched = flatData.length;

  //called on scroll and possibly on mount to fetch more data as the user scrolls and reaches bottom of table
  const fetchMoreOnBottomReached = useCallback(
    (containerRefElement?: HTMLDivElement | null) => {
      if (containerRefElement) {
        const { scrollHeight, scrollTop, clientHeight } = containerRefElement;
        //once the user has scrolled within 400px of the bottom of the table, fetch more data if we can
        if (
          scrollHeight - scrollTop - clientHeight < 400 &&
          !isFetching &&
          totalFetched < totalDBRowCount
        ) {
          fetchNextPage();
        }
      }
    },
    [fetchNextPage, isFetching, totalFetched, totalDBRowCount]
  );

  // When card list is at top and user scrolls up (swipe down), propagate to outer so filters/header come back
  useEffect(() => {
    if (!isMobile) return;
    const inner = mobileCardsContainerRef.current;
    if (!inner) return;
    const onTouchStart = (e: TouchEvent) => {
      const t = e.touches[0];
      if (t) touchStartYRef.current = t.clientY;
    };
    const onTouchMove = (e: TouchEvent) => {
      const t = e.touches[0];
      const outer = scrollContainerRef.current;
      if (!t || !outer || inner.scrollTop > 0) return;
      const dy = t.clientY - touchStartYRef.current;
      if (dy <= 0) return;
      outer.scrollTop -= dy;
      touchStartYRef.current = t.clientY;
      e.preventDefault();
    };
    const onWheel = (e: WheelEvent) => {
      const outer = scrollContainerRef.current;
      if (!outer || inner.scrollTop > 0) return;
      if (e.deltaY >= 0) return;
      outer.scrollTop += e.deltaY;
      e.preventDefault();
    };
    inner.addEventListener("touchstart", onTouchStart, { passive: true });
    inner.addEventListener("touchmove", onTouchMove, { passive: false });
    inner.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      inner.removeEventListener("touchstart", onTouchStart);
      inner.removeEventListener("touchmove", onTouchMove);
      inner.removeEventListener("wheel", onWheel);
    };
  }, [isMobile]);

  const setIndustriesFilter = useCallback((industryList: string[]) => {
    setColumnFilters((prev) => {
      const rest = prev.filter((f) => f.id !== "industries");
      if (industryList.length === 0) return rest;
      return [...rest, { id: "industries", value: industryList }];
    });
  }, []);

  const activeFilterCount = useMemo(() => {
    let n = 0;
    if (selectedIndustry?.length) n += selectedIndustry.length;
    if (globalFilter?.trim()) n += 1;
    const [min, max] = fundingUsdRange;
    if (min != null || max != null) n += 1;
    return n;
  }, [selectedIndustry, globalFilter, fundingUsdRange]);

  //scroll to top of table when sorting or filters change
  useEffect(() => {
    //scroll to the top of the table when the sorting changes
    try {
      rowVirtualizerInstanceRef.current?.scrollToIndex?.(0);
    } catch (error) {
      console.error(error);
    }
  }, [sorting, columnFilters, globalFilter]);

  // Persist sorting, search, industry filter, and funding range in URL for shareable links
  useEffect(() => {
    const next = buildSearchParamsFromState(columnFilters, globalFilter, sorting);
    setSearchParams(next, { replace: true });
  }, [columnFilters, globalFilter, sorting, setSearchParams]);

  // Sync state from URL only on browser back/forward (popstate). If we depended on searchParams here,
  // we'd overwrite state with stale params right after we write the URL (e.g. sort toggle would revert).
  useEffect(() => {
    const onPopState = () => {
      const params = new URLSearchParams(window.location.search);
      const parsed = parseTableStateFromSearchParams(params);
      setColumnFilters(parsed.columnFilters);
      setGlobalFilter(parsed.globalFilter);
      setSorting(parsed.sorting);
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  //a check on mount to see if the table is already scrolled to the bottom and immediately needs to fetch more data
  useEffect(() => {
    fetchMoreOnBottomReached(tableContainerRef.current);
  }, [fetchMoreOnBottomReached]);

  // Shrink table container when content is smaller than 80vh to remove the huge gap (desktop)
  // Use a minimum height so that 1 or few results don't collapse to a tiny strip
  const TABLE_MIN_HEIGHT_PX = 280;
  useEffect(() => {
    if (isMobile) return;
    const rafId = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const total = rowVirtualizerInstanceRef.current?.getTotalSize?.();
        if (typeof total === "number" && total > 0) {
          const maxVh = window.innerHeight * 0.8;
          const contentHeight = Math.ceil(total);
          const heightPx = Math.max(TABLE_MIN_HEIGHT_PX, Math.min(contentHeight, maxVh));
          setTableContainerHeight(contentHeight < maxVh ? `${heightPx}px` : "80vh");
        } else {
          setTableContainerHeight("80vh");
        }
      });
    });
    return () => cancelAnimationFrame(rafId);
  }, [isMobile, flatData.length, expanded]);

  const columns = useMemo<MRT_ColumnDef<CompayDetail>[]>(
    () => [
      {
        accessorKey: "logo",
        header: "Logo",
        enableSorting: false,
        Cell: ({ cell }) => {
          return (
            <div className="flex h-auto w-auto items-center gap-5">
              <a
                href={cell.row.original?.logo || "/image-broken.png"}
                target="_blank"
                rel="noopener noreferrer"
              >
                <img
                  src={cell.row.original?.logo || "/image-broken.png"}
                  alt="company-icon"
                  loading="lazy"
                  width={40}
                  height={40}
                  className="h-10 w-10 object-contain"
                />
              </a>
              <button
                type="button"
                onClick={() => openExportModal(cell.row.original)}
                className="rounded-input p-1.5 text-slate-600 transition-colors hover:bg-slate-100 hover:text-brand-600 focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-300 dark:hover:bg-slate-700 dark:hover:text-brand-400"
                aria-label="Export to Notion"
              >
                <ArrowTopRightOnSquareIcon className="h-5 w-5" />
              </button>
            </div>
          );
        },
      },
      {
        accessorKey: "name",
        header: "Name",
        Cell: ({ cell }) => (
          <>
            {cell.row.original.website ? (
              <a
                className="link-underline"
                href={cell.row.original.website}
                target="_blank"
                rel="noopener noreferrer"
              >
                {cell.row.original.name}
              </a>
            ) : (
              cell.row.original.name
            )}
          </>
        ),
      },
      {
        accessorKey: "funding",
        header: "Funding",
        Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>,
      },
      {
        accessorKey: "created_at",
        header: "Created",
        Cell: ({ cell }) => {
          const value = cell.getValue() as Date;
          return (
            <>
              {value
                ? differenceInMinutes(new Date(), value) < 60
                  ? formatDistance(value, new Date(), { addSuffix: true })
                  : format(value, "yyyy-MM-dd hh:mm a")
                : "-"}
            </>
          );
        },
      },
      {
        accessorKey: "updated_at",
        header: "Updated",
        Cell: ({ cell }) => {
          const value = cell.getValue() as Date;
          return (
            <>
              {value
                ? differenceInMinutes(new Date(), value) < 60
                  ? formatDistance(value, new Date(), { addSuffix: true })
                  : format(value, "yyyy-MM-dd hh:mm a")
                : "-"}
            </>
          );
        },
      },
      {
        accessorKey: "funding_usd",
        header: "Funding USD",
        filterVariant: "range",
        size: 260,
        muiFilterTextFieldProps: {
          sx: { minWidth: 112 },
        },
        Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>,
      },
      {
        accessorKey: "acquired",
        header: "Acquired",
        Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>,
        size: 300,
      },
      {
        accessorKey: "description",
        header: "Description",
        size: 300,
      },
      {
        accessorKey: "industries",
        header: "Industries",
        filterVariant: "multi-select",
        filterSelectOptions: filterIndustry,
        size: 200,
        Cell: ({ cell }) => {
          const _f = cell.row.original.industries;
          return (
            <div>
              {" "}
              {_f && _f.length > 0
                ? _f.map((f) => <div key={`${f}-f`}>{f}</div>)
                : "-"}
            </div>
          );
        },
      },
      {
        accessorKey: "founders",
        header: "Founders",
        size: 200,
        Cell: ({ cell }) => {
          const _f = cell.row.original.founders;
          return (
            <div>
              {" "}
              {_f && _f.length > 0
                ? _f.map((f) => <div key={`${f}-f`}>{f}</div>)
                : "-"}
            </div>
          );
        },
      },
      {
        accessorKey: "lastfunding",
        header: "Last Fund",
        Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>,
      },
      {
        accessorKey: "founded",
        header: "Founded",
        Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>,
      },
      {
        accessorKey: "stocksymbol",
        header: "Stock",
        Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>,
      },
      {
        accessorKey: "website",
        header: "Website",
        Cell: ({ cell }) => (
          <>
            {cell.row.original.website ? (
              <a
                className="link-underline"
                href={cell.row.original.website}
                target="_blank"
                rel="noopener noreferrer"
              >
                {cell.row.original.website}
              </a>
            ) : (
              "-"
            )}
          </>
        ),
        size: 300,
      },
      {
        accessorKey: "crunchbase_url",
        header: "Crunchbase",
        Cell: ({ cell }) => (
          <>
            {cell.row.original.crunchbase_url ? (
              <a
                className="link-underline"
                href={cell.row.original.crunchbase_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {cell.row.original.crunchbase_url}
              </a>
            ) : (
              "-"
            )}
          </>
        ),
        size: 500,
      },
      {
        accessorKey: "tracxn_url",
        header: "Tracxn",
        Cell: ({ cell }) => (
          <>
            {cell.row.original.tracxn_url ? (
              <a
                className="link-underline"
                href={cell.row.original.tracxn_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {cell.row.original.tracxn_url}
              </a>
            ) : (
              "-"
            )}
          </>
        ),
        size: 500,
      },
      {
        header: "Action",
        Cell: ({ cell }) => {
          const [loading, setLoading] = useState(false);
          const [retried, setRetried] = useState<"init" | "done" | "error">(
            "init"
          );
          function handleClick() {
            setLoading(true);
            const retryPromise = crunchyClient.post("/api/crawl/create", {
              url: [cell.row.original.crunchbase_url],
            });
            toast.promise(retryPromise, {
              loading: "Pushing to queue",
              success: "Pushed to queue",
              error: "Error pushing to queue",
            });
            retryPromise
              .then(() => {
                setRetried("done");
              })
              .catch(() => {
                setRetried("error");
              })
              .finally(() => setLoading(false));
          }

          return (
            <>
              <LoadingButton
                size="small"
                onClick={handleClick}
                disabled={retried === "done"}
                loading={loading}
                loadingIndicator="Pushing.."
                color={
                  retried === "done"
                    ? "success"
                    : retried === "error"
                      ? "error"
                      : "primary"
                }
                variant="outlined"
              >
                {retried === "init"
                  ? "Retry"
                  : retried === "done"
                    ? "Pushed🔥"
                    : "Error!"}
              </LoadingButton>
            </>
          );
        },
        size: 500,
      },
    ],
    [filterIndustry]
  );

  const table = useMaterialReactTable({
    columns,
    data: flatData,
    enablePagination: false,
    enableRowNumbers: true,
    enableRowVirtualization: true,
    manualFiltering: true,
    manualSorting: true,
    muiSkeletonProps: {
      animation: "wave",
    },
    enableColumnPinning: true,
    muiTableContainerProps: {
      ref: tableContainerRef,
      sx: {
        maxHeight: "80vh",
        height: tableContainerHeight,
        borderRadius: 2,
      },
      onScroll: (event: UIEvent<HTMLDivElement>) =>
        fetchMoreOnBottomReached(event.target as HTMLDivElement),
    },
    onExpandedChange: (updater) =>
      setExpanded((prev) => (typeof updater === "function" ? updater(prev) : updater)),
    muiToolbarAlertBannerProps: isError
      ? {
        color: "error",
        children: "Error loading data",
      }
      : undefined,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    onSortingChange: setSorting,
    enableExpandAll: false,
    muiDetailPanelProps: () => ({
      sx: {
        py: 0,
        verticalAlign: "top",
        width: "100%",
        maxWidth: "100%",
        overflow: "hidden",
      },
    }),
    renderDetailPanel: ({ row }) => {
      const c = row.original as unknown as Record<string, unknown>;
      const entries = isMobile ? getSortedDetailEntriesForMobile(c) : getSortedDetailEntries(c);
      const useful = entries.filter((e) => !isMetadataDetailKey(e.key));
      const rest = entries.filter((e) => isMetadataDetailKey(e.key));
      const renderField = ({ key, value }: { key: string; value: unknown }, index: number) => {
        const isLongText = key === "long_description" || key === "description";
        return (
          <div
            key={`${row.original._id}-${key}-${index}`}
            className="flex min-w-0 flex-col gap-0.5"
          >
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              {detailKeyToLabel(key)}:
            </span>
            <span
              className={
                isLongText
                  ? "max-w-prose min-w-0 overflow-hidden break-words text-sm text-slate-800 dark:text-slate-200"
                  : "min-w-0 overflow-hidden break-words break-all text-sm text-slate-800 dark:text-slate-200"
              }
            >
              {formatDetailValue(value)}
            </span>
          </div>
        );
      };
      return (
        <div className="w-full min-w-0 rounded-lg border border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100/80 p-4 dark:border-slate-600 dark:from-slate-800/80 dark:to-slate-900/80">
          <div className="flex flex-col gap-4 sm:flex-row sm:gap-6">
            <div className="flex h-32 w-32 shrink-0 items-center">
              <a
                href={(c.logo as string) || "/image-broken.png"}
                target="_blank"
                rel="noopener noreferrer"
                className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-600 dark:bg-slate-800"
              >
                <img
                  src={(c.logo as string) || "/image-broken.png"}
                  alt=""
                  loading="lazy"
                  width={100}
                  height={100}
                  className="h-[100px] w-[100px] object-contain p-1"
                />
              </a>
            </div>
            <div className="flex min-w-0 flex-1 flex-col gap-4 sm:flex-row sm:gap-3">
              <div className="flex min-w-0 max-w-2xl flex-col gap-3 sm:shrink-0">
                {useful.map((entry, index) => renderField(entry, index))}
              </div>
              <div className="flex min-w-0 flex-1 flex-col gap-3">
                {rest.map((entry, index) => renderField(entry, index))}
              </div>
            </div>
          </div>
        </div>
      );
    },
    renderBottomToolbarCustomActions: () => (
      <Typography className="text-sm text-slate-600 dark:text-slate-400">
        Fetched {totalFetched} of {totalDBRowCount} total rows.
      </Typography>
    ),
    state: {
      columnFilters,
      expanded,
      globalFilter,
      isLoading,
      showAlertBanner: isError,
      showSkeletons: isFetching,
      sorting,
    },
    rowVirtualizerInstanceRef, //get access to the virtualizer instance
    rowVirtualizerOptions: { overscan: 4 },
  });

  const HEADER_HEIGHT_PX = 56;

  useEffect(() => {
    if (!isMobile) setHeaderHidden(false);
    return () => setHeaderHidden(false);
  }, [isMobile, setHeaderHidden]);

  return (
    <div
      className={`mb-6 mt-4 w-full min-w-0 md:mt-6 ${isMobile ? "overflow-visible" : "overflow-x-clip"}`}
    >
      {!isMobile && (
        <>
          <div className="mb-2 flex min-w-0 flex-wrap items-center gap-3 md:gap-4">
            <h1 className="page-title text-lg sm:text-xl">Company Details</h1>
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-sm font-semibold text-slate-700 dark:bg-slate-600 dark:text-slate-200">
              {totalDBRowCount}
            </span>
            <Button
              onClick={() => setOpenCrawlModal(true)}
              variant="contained"
              color="primary"
              size="medium"
              sx={{
                textTransform: "none",
                fontWeight: 600,
                borderRadius: 2,
                px: 2,
                py: 1,
                boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
              }}
            >
              Create Crawl
            </Button>
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel id="industry-sort-by-label">Industry Sort By</InputLabel>
              <Select
                labelId="industry-sort-by-label"
                id="industry-sort-by-select"
                value={industryOptionSortBy}
                label="Industry Sort By"
                onChange={(e) =>
                  setIndustryOptionSortBy(e.target.value as IndustryOptionSortBy)
                }
                sx={{ borderRadius: 2 }}
              >
                <MenuItem value="default">Default</MenuItem>
                <MenuItem value="alphabetical">Alphabetical</MenuItem>
                <MenuItem value="industryCount">Industry Count</MenuItem>
              </Select>
            </FormControl>
            {isLoading && (
              <span className="relative flex h-3 w-3" aria-hidden>
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-brand-500" />
              </span>
            )}
          </div>
          <div className="mb-2">
            <Pending />
          </div>
        </>
      )}

      {isMobile ? (
        /* Level 1: outer scroll – header/filter chrome; Level 2: card container has its own scroll */
        <div
          ref={scrollContainerRef}
          className="fixed left-0 right-0 z-0 overflow-x-hidden overflow-y-auto overscroll-contain bg-[#f8fafc] dark:bg-[#0f172a]"
          style={{
            top: HEADER_HEIGHT_PX,
            height: `calc(100vh - ${HEADER_HEIGHT_PX}px)`,
          }}
          role="main"
          aria-label="Company list"
        >
          {/* Chrome: title, pending, filter – scrolls away with outer */}
          <div className="min-w-0 px-4 pt-4 pb-4">
            <div className="mb-2 flex min-w-0 flex-wrap items-center gap-3">
              <h1 className="page-title text-lg sm:text-xl">Company Details</h1>
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-sm font-semibold text-slate-700 dark:bg-slate-600 dark:text-slate-200">
                {totalDBRowCount}
              </span>
              <Button
                onClick={() => setOpenCrawlModal(true)}
                variant="contained"
                color="primary"
                size="medium"
                sx={{
                  textTransform: "none",
                  fontWeight: 600,
                  borderRadius: 2,
                  px: 2,
                  py: 1,
                  boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                }}
              >
                Create Crawl
              </Button>
              {isLoading && (
                <span className="relative flex h-3 w-3" aria-hidden>
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-75" />
                  <span className="relative inline-flex h-3 w-3 rounded-full bg-brand-500" />
                </span>
              )}
            </div>
            <div className="mb-2">
              <Pending />
            </div>
            <div className="mt-4">
              <MobileFilters
                search={globalFilter ?? ""}
                onSearchChange={setGlobalFilter}
                sorting={sorting}
                onSortingChange={setSorting}
                industryOptions={filterIndustry}
                selectedIndustries={selectedIndustry ?? []}
                onIndustriesChange={setIndustriesFilter}
                industryOptionSortBy={industryOptionSortBy}
                onIndustryOptionSortByChange={setIndustryOptionSortBy}
                fundingUsdMin={fundingUsdRange[0]}
                fundingUsdMax={fundingUsdRange[1]}
                onFundingUsdChange={setFundingUsdFilter}
                totalCount={totalDBRowCount}
                activeFilterCount={activeFilterCount}
              />
            </div>
          </div>
          <div className="h-0 w-full shrink-0" aria-hidden />
          {/* Level 2: card root container – own scroll, fills viewport when chrome is scrolled away */}
          <div
            ref={mobileCardsContainerRef}
            className="min-h-0 shrink-0 overflow-x-hidden overflow-y-auto overscroll-contain bg-[#f8fafc] dark:bg-[#0f172a]"
            style={{
              height: `calc(100vh - ${HEADER_HEIGHT_PX}px)`,
            }}
            onScroll={(e) => fetchMoreOnBottomReached(e.currentTarget)}
            aria-label="Company cards"
          >
            <div className="min-w-0 px-4 pb-6 pt-2">
              {isLoading ? (
                <div className="flex w-full min-w-0 max-w-full flex-col gap-3">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className="h-24 animate-pulse rounded-xl bg-slate-200 dark:bg-slate-700"
                    />
                  ))}
                </div>
              ) : isError ? (
                <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
                  Error loading data
                </p>
              ) : (
                <div className="flex w-full min-w-0 max-w-full flex-col gap-3">
                  {flatData.map((company) => (
                    <CompanyCard
                      key={company._id}
                      company={company}
                      onExport={openExportModal}
                      onCardClick={(c) => setDetailModalCompany(c)}
                    />
                  ))}
                  {isFetching && totalFetched > 0 && (
                    <div className="flex justify-center py-4">
                      <span className="text-sm text-slate-500 dark:text-slate-400">
                        Loading more…
                      </span>
                    </div>
                  )}
                  {totalFetched > 0 && totalFetched >= totalDBRowCount && (
                    <p className="py-2 text-center text-xs text-slate-500 dark:text-slate-400">
                      Fetched {totalFetched} of {totalDBRowCount} companies.
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <>
          <hr className="my-4 border-0 bg-slate-200 dark:bg-slate-600" style={{ height: 1 }} />
          <div className="card-base p-0 overflow-hidden">
            <MaterialReactTable table={table} />
          </div>
        </>
      )}

      {modalIsOpen === true && (
        <ExportToNotion
          modalIsOpen={modalIsOpen}
          modalData={modalData}
          setModal={setModal}
        />
      )}
      {crawlModalIsOpen === true && (
        <CreateCrawl
          modalIsOpen={crawlModalIsOpen}
          setModal={setOpenCrawlModal}
        />
      )}
      <CompanyDetailModal
        company={detailModalCompany}
        isOpen={detailModalCompany != null}
        onClose={() => setDetailModalCompany(null)}
      />
    </div>
  );
};
