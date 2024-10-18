import { ArrowTopRightOnSquareIcon } from "@heroicons/react/24/solid";
import LoadingButton from "@mui/lab/LoadingButton";
import { Button, Typography } from "@mui/material";
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
import Image from "next/image";
import Link from "next/link";
import {
  type UIEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import toast, { Toaster } from "react-hot-toast";
import { isUrl } from "~/utils";
import crunchyClient from "~/utils/crunchyClient";
import { type CompayDetail } from "~/utils/types";
import { getBaseURL } from "../../utils/baseUrl";
import CreateCrawl from "../CreateCrawl";
import ExportToNotion from "../ExportNotionModal";
import { Pending } from "../Pending";
import useIndustryList from "~/hooks/industryList";

type UserApiResponse = {
  results: Array<CompayDetail>;
  count: number;
  next?: string;
  previous?: string;
};

export const CompanyDetails = ({ industries }: { industries: string[] }) => {
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

  const selectedIndustry = useMemo(
    () => columnFilters.find((f) => f.id === "industries")?.value as string[],
    [columnFilters]
  );

  const filterIndustry = useIndustryList(industries, selectedIndustry);

  console.log("filterIndustry:", filterIndustry.length);

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
              <Link href={cell.row.original?.logo || "/image-broken.png"}>
                <Image
                  src={cell.row.original?.logo || "/image-broken.png"}
                  alt="company-icon"
                  loading="lazy"
                  width={40}
                  height={40}
                />
              </Link>
              <button onClick={() => openExportModal(cell.row.original)}>
                <ArrowTopRightOnSquareIcon className="h-5 w-5 fill-gray-800" />
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
              <Link
                className="text-blue-500 underline "
                href={cell.row.original.website}
              >
                {" "}
                {cell.row.original.name}{" "}
              </Link>
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
              <Link
                className="text-blue-500 underline "
                href={cell.row.original.website}
              >
                {" "}
                {cell.row.original.website}{" "}
              </Link>
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
              <Link
                className="text-blue-500 underline "
                href={cell.row.original.crunchbase_url}
              >
                {" "}
                {cell.row.original.crunchbase_url}{" "}
              </Link>
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
      ref: tableContainerRef, //get access to the table container element
      sx: { maxHeight: "80vh" }, //give the table a max height
      onScroll: (event: UIEvent<HTMLDivElement>) =>
        fetchMoreOnBottomReached(event.target as HTMLDivElement), //add an event listener to the table container element
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
        <div className="grid w-[100vw] grid-cols-2 content-center gap-4 rounded-md border-2 border-solid border-slate-300 bg-white p-2">
          <div className="flex h-32 w-32 items-center">
            <Link href={row.original?.logo || "/image-broken.png"}>
              <Image
                src={row.original?.logo || "/image-broken.png"}
                alt="company-icon"
                loading="lazy"
                width={100}
                height={100}
              />
            </Link>
          </div>
          {Object.entries(row.original).map(([key, value], index) => {
            return (
              <div
                key={`${row.original._id}-${index}-expand`}
                className="flex flex-col"
              >
                <span className="text-base capitalize text-gray-500">
                  {key}:
                </span>
                <span className="overflow-hidden break-words text-gray-500">
                  {!value ? (
                    "-"
                  ) : typeof value === "string" ? (
                    isUrl(value) ? (
                      <a
                        href={value}
                        target="_blank"
                        className="text-blue-500 underline"
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
                          <div>
                            <Link
                              key={idx}
                              href={item}
                              target="_blank"
                              className="text-blue-500 underline"
                            >
                              {item}
                            </Link>
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
                    value
                  )}
                </span>
              </div>
            );
          })}
        </div>
      );
    },
    renderBottomToolbarCustomActions: () => (
      <Typography className="text-gray-400">
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
    <div className="mb-2 mt-2 rounded-md bg-white p-5 shadow-2xl">
      <div className="flex items-center gap-2">
        <h1 className="mr-5 text-center text-xl text-gray-400">
          Company Details
        </h1>
        <h3 className="mr-5 text-center text-lg text-gray-400">
          {totalDBRowCount}
        </h3>
        <Button
          onClick={() => {
            setOpenCrawlModal(true);
          }}
          variant="outlined"
          color="primary"
        >
          Create Crawl
        </Button>
        <span className="relative flex h-3 w-3">
          {isLoading && (
            <>
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75"></span>
              <span className="relative inline-flex h-3 w-3 rounded-full bg-sky-500"></span>
            </>
          )}
        </span>
      </div>
      <Pending />
      <hr className="my-3 h-px border-0 bg-gray-200 " />

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
      <Toaster />
    </div>
  );
};
