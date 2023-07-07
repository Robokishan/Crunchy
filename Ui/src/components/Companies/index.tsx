import {
    MaterialReactTable,
    type MRT_ColumnDef,
    type MRT_Virtualizer
} from 'material-react-table';
import Image from "next/image";
import Link from "next/link";
import { useMemo, useRef } from "react";
import { type CompayDetail } from "~/utils/types";
import SearchInput from "../SearchInput";



export const CompanyDetails = ({ isLoading = false, companyDetails, onSearch }: { isLoading?: boolean, companyDetails: Array<CompayDetail>, onSearch: (value: string) => void }) => {


    const columns = useMemo<MRT_ColumnDef<CompayDetail>[]>(
        () => [
            {
                accessorKey: 'logo',
                header: 'Logo',
                Cell: ({ cell }) => (
                    <>
                        <div className="flex items-center h-9 w-9">
                            <Image src={cell.row.original.logo} alt="company-icon" width={100} height={100} />
                        </div>
                    </>
                )
            },
            {
                accessorKey: 'name',
                header: 'Name',
                Cell: ({ cell }) => <>
                    {cell.row.original.website ?
                        <Link className="text-blue-500 underline " href={cell.row.original.website}>  {cell.row.original.name} </Link> : cell.row.original.name}
                </>,
            },
            {
                accessorKey: 'funding',
                header: 'Funding',
                Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>
            },
            {
                accessorKey: 'acquired',
                header: 'Acquired',
                Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>,
                size: 300,
            },
            {
                accessorKey: 'description',
                header: 'Description',
                size: 300,
            },
            {
                accessorKey: 'founders',
                header: 'Founders',
                size: 200,
                Cell: ({ cell }) => {
                    const _f = cell.row.original.founders
                    return <div> {_f && _f.length > 0 ?
                        _f.map(f => <div key={`${f}-f`}>{f}</div>)
                        : "-"}</div>
                }
            },
            {
                accessorKey: "lastfunding",
                header: "Last Fund",
                Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>
            },
            {
                accessorKey: 'founded',
                header: 'Founded',
                Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>
            },
            {
                accessorKey: 'stocksymbol',
                header: 'Stock',
                Cell: ({ cell }) => <>{cell.getValue() ?? "-"}</>


            },
            {
                accessorKey: 'website',
                header: 'Website',
                Cell: ({ cell }) => <>
                    {cell.row.original.website ?
                        <Link className="text-blue-500 underline " href={cell.row.original.website}>  {cell.row.original.website} </Link> : "-"}
                </>,
                size: 300,
            },
            {
                accessorKey: 'crunchbase_url',
                header: 'Crunchbase',
                Cell: ({ cell }) => <>
                    {cell.row.original.crunchbase_url ?
                        <Link className="text-blue-500 underline " href={cell.row.original.crunchbase_url}> {cell.row.original.crunchbase_url} </Link> : "-"}
                </>,
                size: 500,
            },

        ],
        [],);



    const rowVirtualizerInstanceRef =
        useRef<MRT_Virtualizer<HTMLDivElement, HTMLTableRowElement>>(null);


    return (
        <div className="mb-2 mt-2 rounded-md bg-white p-5 shadow-2xl">
            <span className="relative flex h-3 w-3">
                {isLoading && (
                    <>
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75"></span>
                        <span className="relative inline-flex h-3 w-3 rounded-full bg-sky-500"></span>
                    </>
                )}
            </span>

            <div className="flex items-center gap-2">
                <h1 className="mr-5 text-center text-xl text-gray-400">Company Details</h1>
                <h3 className="mr-5 text-center text-lg text-gray-400">{companyDetails.length}</h3>
            </div>
            <hr className="my-3 h-px border-0 bg-gray-200 " />

            <SearchInput onSearch={onSearch} />
            <div className="overflow-auto max-h-[85vh]">
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
                        'mrt-row-expand': {
                            muiTableHeadCellProps: {
                                align: 'right',
                            },
                            muiTableBodyCellProps: {
                                align: 'right',
                            },
                        },
                    }}
                    enableRowVirtualization
                    // muiTableContainerProps={{ sx: { maxHeight: '900px' } }}
                    renderDetailPanel={({ row }) => (
                        <div
                            className="grid w-[80vw] bg-white rounded-md grid-cols-2 content-center gap-4 p-2 border-slate-300 border-solid border-2"
                        >
                            <div className="flex items-center h-32 w-32">
                                <Image src={row.original.logo} alt="company-icon" width={100} height={100} />
                            </div>
                            {Object.entries(row.original).map(([key, value]) => {
                                return <div key={`${row.original.name}-expand`} className="flex flex-col">
                                    <span className="capitalize text-base text-gray-500">{key}:</span>
                                    <span className="text-gray-500">{!value ? "-" : typeof value === 'string' ? value : Array.isArray(value) ? value.join(', ') : value}</span>
                                </div>
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
        </div >
    );
};
