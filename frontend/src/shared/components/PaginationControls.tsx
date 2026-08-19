import { AppSelect } from "./AppSelect";

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100].map((value) => ({
  value: String(value),
  label: `${value} rows`,
}));

type PageToken = number | "ellipsis-left" | "ellipsis-right";

const buildPageNumbers = (page: number, totalPages: number): PageToken[] => {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, index) => index + 1);
  if (page <= 4) return [1, 2, 3, 4, 5, "ellipsis-right", totalPages];
  if (page >= totalPages - 3) {
    return [1, "ellipsis-left", totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
  }
  return [1, "ellipsis-left", page - 1, page, page + 1, "ellipsis-right", totalPages];
};

interface PaginationControlsProps {
  page: number;
  pageSize: number;
  total: number;
  itemLabel: string;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  isLoading?: boolean;
  className?: string;
}

export function PaginationControls({
  page,
  pageSize,
  total,
  itemLabel,
  onPageChange,
  onPageSizeChange,
  isLoading = false,
  className = "",
}: PaginationControlsProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(Math.max(page, 1), totalPages);
  const from = total === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const to = Math.min(safePage * pageSize, total);
  const pageNumbers = buildPageNumbers(safePage, totalPages);

  return (
    <div className={`flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between ${className}`}>
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-xs text-[#4C4736]">
          Showing {from}–{to} of {total} {itemLabel}
        </p>
        <AppSelect
          value={String(pageSize)}
          onValueChange={(value) => onPageSizeChange(Number(value))}
          ariaLabel={`${itemLabel} rows per page`}
          options={PAGE_SIZE_OPTIONS}
          className="w-32"
          placement="top"
        />
      </div>

      <nav aria-label={`${itemLabel} pagination`} className="flex flex-wrap items-center gap-1.5">
        <button
          type="button"
          disabled={safePage <= 1 || isLoading}
          onClick={() => onPageChange(Math.max(1, safePage - 1))}
          className="rounded-lg border border-[#CEC6B0]/60 px-3 py-2 text-xs font-semibold text-[#1A1C1C] transition hover:bg-[#F4F3F3] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Previous
        </button>
        {pageNumbers.map((token) =>
          typeof token === "number" ? (
            <button
              key={token}
              type="button"
              aria-current={token === safePage ? "page" : undefined}
              disabled={isLoading}
              onClick={() => onPageChange(token)}
              className={`h-9 min-w-9 rounded-lg px-2 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${
                token === safePage
                  ? "bg-[#8F740D] text-white"
                  : "border border-[#CEC6B0]/60 text-[#1A1C1C] hover:bg-[#F4F3F3]"
              }`}
            >
              {token}
            </button>
          ) : (
            <span key={token} className="px-1 text-xs text-[#756F60]" aria-hidden="true">
              …
            </span>
          ),
        )}
        <button
          type="button"
          disabled={safePage >= totalPages || isLoading}
          onClick={() => onPageChange(Math.min(totalPages, safePage + 1))}
          className="rounded-lg border border-[#CEC6B0]/60 px-3 py-2 text-xs font-semibold text-[#1A1C1C] transition hover:bg-[#F4F3F3] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next
        </button>
      </nav>
    </div>
  );
}
