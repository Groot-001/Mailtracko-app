import { useMemo } from "react";
import { flexRender } from "@tanstack/react-table";
import {
  getCoreRowModel,
  getPaginationRowModel,
  useLegacyTable,
} from "@tanstack/react-table/legacy";
import type { LegacyColumnDef } from "@tanstack/react-table/legacy";

import { PaginationControls } from "./PaginationControls";

interface DataPreviewTableProps {
  headers: string[];
  rows: string[][];
  itemLabel?: string;
  className?: string;
}

/**
 * Shared read-only table for import previews (CSV and Google Sheets).
 * Builds columns dynamically from the sheet headers and paginates through the
 * rows so both import surfaces behave identically.
 */
export function DataPreviewTable({
  headers,
  rows,
  itemLabel = "rows",
  className = "",
}: DataPreviewTableProps) {
  const columns = useMemo<LegacyColumnDef<Record<string, string>>[]>(
    () =>
      headers.map((header) => ({
        accessorKey: header,
        header,
        cell: (info) => info.getValue() as string,
      })),
    [headers],
  );

  const data = useMemo<Record<string, string>[]>(
    () =>
      rows.map((row) =>
        Object.fromEntries(headers.map((header, index) => [header, row[index] ?? ""])),
      ),
    [headers, rows],
  );

  const table = useLegacyTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageIndex: 0,
        pageSize: 10,
      },
    },
  });

  const { pageIndex, pageSize } = table.getState().pagination;

  return (
    <div className={`mt-2 space-y-3 ${className}`}>
      <div className="overflow-auto rounded-2xl border border-[#CEC6B0]/50">
        <table className="min-w-full bg-white text-sm text-[#1A1C1C]">
          <thead className="bg-[#FBFAF6] text-left text-[#4C4736]">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="whitespace-nowrap px-3 py-2 font-bold">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="odd:bg-white even:bg-[#FBFAF6]">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="whitespace-nowrap px-3 py-2">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <PaginationControls
        page={pageIndex + 1}
        pageSize={pageSize}
        total={table.getRowCount()}
        itemLabel={itemLabel}
        onPageChange={(page) => table.setPageIndex(page - 1)}
        onPageSizeChange={(size) => table.setPageSize(size)}
      />
    </div>
  );
}