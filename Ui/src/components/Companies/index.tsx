import {
  MaterialReactTable,
  type MRT_ColumnDef,
  type MRT_Virtualizer,
} from "material-react-table";
import Image from "next/image";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { type CompayDetail } from "~/utils/types";
import SearchInput from "../SearchInput";
import { ArrowTopRightOnSquareIcon } from "@heroicons/react/24/solid";
import ExportToNotion from "../ExportNotionModal";

export const CompanyDetails = ({
  isLoading = false,
  companyDetails,
  onSearch,
}: {
  isLoading?: boolean;
  companyDetails: Array<CompayDetail>;
  onSearch: (value: string) => void;
}) => {
  const [modalIsOpen, setModal] = useState(false);
  const [modalData, setModalData] = useState();

  const openExportModal = useCallback(
    (_data: any) => {
      setModalData(_data);
      setModal(true);
    },
    [modalIsOpen]
  );

  const columns = useMemo<MRT_ColumnDef<CompayDetail>[]>(
    () => [
      {
        accessorKey: "logo",
        header: "Logo",
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

  const rowVirtualizerInstanceRef =
    useRef<MRT_Virtualizer<HTMLDivElement, HTMLTableRowElement>>(null);

  return (
    <div className="mb-2 mt-2 rounded-md bg-white p-5 shadow-2xl">
      <div className="flex items-center gap-2">
        <h1 className="mr-5 text-center text-xl text-gray-400">
          Company Details
        </h1>
        <h3 className="mr-5 text-center text-lg text-gray-400">
          {companyDetails.length}
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

      <SearchInput onSearch={onSearch} />
      <div className="max-h-[85vh] overflow-auto">
        <MaterialReactTable
          columns={columns}
          data={companyDetails}
          // defaultDisplayColumn={{ enableResizing: true }}
          enableBottomToolbar={false}
          enableColumnResizing
          // enableColumnVirtualization
          enableGlobalFilterModes
          enablePagination={false}
          enablePinning
          displayColumnDefOptions={{
            "mrt-row-expand": {
              muiTableHeadCellProps: {
                align: "right",
              },
              muiTableBodyCellProps: {
                align: "right",
              },
            },
          }}
          enableRowVirtualization
          // muiTableContainerProps={{ sx: { maxHeight: '900px' } }}
          renderDetailPanel={({ row }) => (
            <div className="grid w-[80vw] grid-cols-2 content-center gap-4 rounded-md border-2 border-solid border-slate-300 bg-white p-2">
              <div className="flex h-32 w-32 items-center">
                {row.original?.logo && (
                  <Image
                    src={row.original.logo}
                    alt="company-icon"
                    width={100}
                    height={100}
                  />
                )}
              </div>
              {Object.entries(row.original).map(([key, value]) => {
                return (
                  <div
                    key={`${row.original.name}-${row.original._id}-expand`}
                    className="flex flex-col"
                  >
                    <span className="text-base capitalize text-gray-500">
                      {key}:
                    </span>
                    <span className="text-gray-500">
                      {!value
                        ? "-"
                        : typeof value === "string"
                        ? value
                        : Array.isArray(value)
                        ? value.join(", ")
                        : value}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
          //   onSortingChange={setSorting}
          //   state={{ isLoading, sorting }}
          rowVirtualizerInstanceRef={rowVirtualizerInstanceRef} //optional
          rowVirtualizerProps={{ overscan: 5 }} //optionally customize the row virtualizer
          columnVirtualizerProps={{ overscan: 2 }} //optionally customize the column virtualizer
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
