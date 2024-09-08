import { ArrowTopRightOnSquareIcon } from "@heroicons/react/24/solid";
import { Typography } from '@mui/material';
import {
  useInfiniteQuery
} from "@tanstack/react-query";
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
import { type CompayDetail } from "~/utils/types";
import ExportToNotion from "../ExportNotionModal";
import SearchInput from "../SearchInput";

type UserApiResponse = {
  results: Array<CompayDetail>;
  count: number;
};

export const CompanyDetails = () => {
  const tableContainerRef = useRef<HTMLDivElement>(null); //we can get access to the underlying TableContainer element and react to its scroll events
  const rowVirtualizerInstanceRef =
    useRef<MRT_RowVirtualizer<HTMLDivElement, HTMLTableRowElement>>(null);
  const [modalIsOpen, setModal] = useState(false);
  const [modalData, setModalData] = useState();
  const [columnFilters, setColumnFilters] = useState<MRT_ColumnFiltersState>(
    []
  );
  const [globalFilter, setGlobalFilter] = useState<string>();
  const [sorting, setSorting] = useState<MRT_SortingState>([{
    id: "created_at",
    desc: true,
  }]);

  const { data, fetchNextPage, isError, isFetching, isLoading } =
    useInfiniteQuery<UserApiResponse>({
      queryKey: [
        "table-data",
        columnFilters, //refetch when columnFilters changes
        globalFilter, //refetch when globalFilter changes
        sorting, //refetch when sorting changes
      ],
      queryFn: async ({ pageParam }) => {
        const url = new URL(
          "/public/comp",
          process.env.NODE_ENV === "production"
            ? "https://www.material-react-table.com"
            : "http://localhost:8001"
        );
        url.searchParams.set("page", `${(pageParam as number) ?? 1}`);
        url.searchParams.set("filters", JSON.stringify(columnFilters ?? []));
        url.searchParams.set("search", (globalFilter as string) ?? null);
        url.searchParams.set("sorting", JSON.stringify(sorting ?? []));

        const response = await fetch(url.href);
        const json = (await response.json()) as UserApiResponse;
        return json;
      },
      initialPageParam: 1,
      getNextPageParam: (_lastGroup, groups) => groups.length,
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
        enableSorting:false,
        Cell: ({ cell }) => (
          <>
            <div className="flex h-auto w-auto items-center gap-5">
              {cell.row?.original?.logo && (
                <Image
                  src={cell.row.original.logo}
                  alt="company-icon"
                  width={30}
                  height={30}
                />
              )}
              <button onClick={() => openExportModal(cell.row.original)}>
                <ArrowTopRightOnSquareIcon className="h-5 w-5 fill-gray-800" />
              </button>
            </div>
          </>
        ),
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
        Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>,
      },
      {
        accessorKey: "updated_at",
        header: "Updated",
        Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>,
      },
      {
        accessorKey: "funding_usd",
        header: "Funding USD",
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
    ],
    []
  );

  const table = useMaterialReactTable({
    columns,
    data: flatData,
    enablePagination: false,
    enableRowNumbers: true,
    enableRowVirtualization: true,
    manualFiltering: true,
    manualSorting: true,
    muiTableContainerProps: {
      ref: tableContainerRef, //get access to the table container element
      sx: { maxHeight: "600px" }, //give the table a max height
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
    renderBottomToolbarCustomActions: () => (
      <Typography>
        Fetched {totalFetched} of {totalDBRowCount} total rows.
      </Typography>
    ),
    state: {
      columnFilters,
      globalFilter,
      isLoading,
      showAlertBanner: isError,
      showProgressBars: isFetching,
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
        <span className="relative flex h-3 w-3">
          {isLoading && (
            <>
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75"></span>
              <span className="relative inline-flex h-3 w-3 rounded-full bg-sky-500"></span>
            </>
          )}
        </span>
      </div>
      <hr className="my-3 h-px border-0 bg-gray-200 " />

      {/* <SearchInput onSearch={onSearch} /> */}
      <div className="max-h-[85vh] overflow-auto">
        <MaterialReactTable
          table={table}
        />
      </div>
      {modalIsOpen === true && (
        <ExportToNotion
          modalIsOpen={modalIsOpen}
          modalData={modalData}
          setModal={setModal}
        />
      )}
    </div>
  );
};
