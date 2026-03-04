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
import toast from "react-hot-toast";
import { isUrl } from "~/utils";
import crunchyClient from "~/utils/crunchyClient";
import { type CompayDetail } from "~/utils/types";
import { getBaseURL } from "../../utils/baseUrl";
import CreateCrawl from "../CreateCrawl";
import ExportToNotion from "../ExportNotionModal";
import { Pending } from "../Pending";
import useIndustryList, { Industry } from "~/hooks/industryList";

type UserApiResponse = {
  results: Array<CompayDetail>;
  count: number;
  next?: string;
  previous?: string;
};

type IndustryOptionSortBy = "industryCount" | "alphabetical" | "default";

export const CompanyDetails = ({ industries }: { industries: Industry[] }) => {
  const tableContainerRef = useRef<HTMLDivElement>(null); //we can get access to the underlying TableContainer element and react to its scroll events
  const rowVirtualizerInstanceRef =
    useRef<MRT_RowVirtualizer<HTMLDivElement, HTMLTableRowElement>>(null);
  const [modalIsOpen, setModal] = useState(false);
  const [crawlModalIsOpen, setOpenCrawlModal] = useState(false);
  const [modalData, setModalData] = useState();
  const [columnFilters, setColumnFilters] = useState<MRT_ColumnFiltersState>(
    []
  );
  const [globalFilter, setGlobalFilter] = useState<string>();
  const [sorting, setSorting] = useState<MRT_SortingState>([
    {
      id: "created_at",
      desc: true,
    },
  ]);
  const [industryOptionSortBy, setIndustryOptionSortBy] =
    useState<IndustryOptionSortBy>("default");

  const selectedIndustry = useMemo(
    () => columnFilters.find((f) => f.id === "industries")?.value as string[],
    [columnFilters]
  );

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

  //scroll to top of table when sorting or filters change
  useEffect(() => {
    //scroll to the top of the table when the sorting changes
    try {
      rowVirtualizerInstanceRef.current?.scrollToIndex?.(0);
    } catch (error) {
      console.error(error);
    }
  }, [sorting, columnFilters, globalFilter]);

  //a check on mount to see if the table is already scrolled to the bottom and immediately needs to fetch more data
  useEffect(() => {
    fetchMoreOnBottomReached(tableContainerRef.current);
  }, [fetchMoreOnBottomReached]);

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
      sx: { maxHeight: "80vh", borderRadius: 2 },
      onScroll: (event: UIEvent<HTMLDivElement>) =>
        fetchMoreOnBottomReached(event.target as HTMLDivElement),
    },
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
    renderDetailPanel: ({ row }) => {
      return (
        <div className="grid w-full grid-cols-2 gap-4 rounded-panel border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-600 dark:bg-slate-800/50">
          <div className="flex h-32 w-32 items-center">
            <a
              href={row.original?.logo || "/image-broken.png"}
              target="_blank"
              rel="noopener noreferrer"
            >
              <img
                src={row.original?.logo || "/image-broken.png"}
                alt="company-icon"
                loading="lazy"
                width={100}
                height={100}
                className="h-[100px] w-[100px] object-contain"
              />
            </a>
          </div>
          {Object.entries(row.original).map(([key, value], index) => {
            return (
              <div
                key={`${row.original._id}-${index}-expand`}
                className="flex flex-col"
              >
                <span className="text-sm font-medium capitalize text-slate-500 dark:text-slate-400">
                  {key}:
                </span>
                <span className="overflow-hidden break-words text-sm text-slate-700 dark:text-slate-300">
                  {!value ? (
                    "-"
                  ) : typeof value === "string" ? (
                    isUrl(value) ? (
                      <a
                        href={value}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="link-underline"
                      >
                        {value}
                      </a>
                    ) : (
                      value
                    )
                  ) : Array.isArray(value) ? (
                    value.length > 0 ? (
                      value.map((item, idx, arr) =>
                        typeof item === "string" && isUrl(item) ? (
                          <div key={idx}>
                            <a
                              href={item}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="link-underline"
                            >
                              {item}
                            </a>
                          </div>
                        ) : (
                          <>
                            <span key={idx}>{item}</span>
                            {arr.length - 1 !== idx && <span>, </span>}
                          </>
                        )
                      )
                    ) : (
                      "-"
                    )
                  ) : (
                    typeof value === "object"
                      ? JSON.stringify(value)
                      : value
                  )}
                </span>
              </div>
            );
          })}
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
      globalFilter,
      isLoading,
      showAlertBanner: isError,
      showSkeletons: isFetching,
      sorting,
    },
    rowVirtualizerInstanceRef, //get access to the virtualizer instance
    rowVirtualizerOptions: { overscan: 4 },
  });

  return (
    <div className="card-base mx-4 mb-6 mt-6 w-full max-w-[1600px] sm:mx-6 md:mx-auto">
      <div className="flex flex-wrap items-center gap-4">
        <h1 className="page-title">Company Details</h1>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-700 dark:bg-slate-600 dark:text-slate-200">
          {totalDBRowCount}
        </span>
        <Button
          onClick={() => setOpenCrawlModal(true)}
          variant="contained"
          color="primary"
          sx={{
            textTransform: "none",
            fontWeight: 600,
            borderRadius: 2,
            px: 2.5,
            py: 1.25,
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
      <Pending />
      <hr className="my-4 border-0 bg-slate-200 dark:bg-slate-600" style={{ height: 1 }} />

      {/* <SearchInput onSearch={onSearch} /> */}

      <MaterialReactTable table={table} />

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
    </div>
  );
};
