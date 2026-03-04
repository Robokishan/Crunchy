import FilterListIcon from "@mui/icons-material/FilterList";
import {
  Autocomplete,
  Button,
  Drawer,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from "@mui/material";
import { useCallback, useMemo, useState } from "react";
import type { MRT_ColumnFiltersState, MRT_SortingState } from "material-react-table";
import type { DropdownOption } from "material-react-table";

type SortOption = "created_at" | "updated_at" | "funding_usd";
type SortDirection = "desc" | "asc";

const SORT_LABELS: Record<string, string> = {
  "created_at-desc": "Created (newest)",
  "created_at-asc": "Created (oldest)",
  "updated_at-desc": "Updated (newest)",
  "updated_at-asc": "Updated (oldest)",
  "funding_usd-desc": "Funding USD (high to low)",
  "funding_usd-asc": "Funding USD (low to high)",
};

type IndustryOptionSortBy = "industryCount" | "alphabetical" | "default";

interface MobileFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  sorting: MRT_SortingState;
  onSortingChange: (sorting: MRT_SortingState) => void;
  industryOptions: DropdownOption[];
  selectedIndustries: string[];
  onIndustriesChange: (industries: string[]) => void;
  industryOptionSortBy: IndustryOptionSortBy;
  onIndustryOptionSortByChange: (value: IndustryOptionSortBy) => void;
  fundingUsdMin: number | undefined;
  fundingUsdMax: number | undefined;
  onFundingUsdChange: (min: number | undefined, max: number | undefined) => void;
  totalCount: number;
  activeFilterCount: number;
}

export function MobileFilters({
  search,
  onSearchChange,
  sorting,
  onSortingChange,
  industryOptions,
  selectedIndustries,
  onIndustriesChange,
  industryOptionSortBy,
  onIndustryOptionSortByChange,
  fundingUsdMin,
  fundingUsdMax,
  onFundingUsdChange,
  totalCount,
  activeFilterCount,
}: MobileFiltersProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  const sortId = (sorting[0]?.id ?? "created_at") as SortOption;
  const sortDir = (sorting[0]?.desc !== false ? "desc" : "asc") as SortDirection;
  const sortKey = `${sortId}-${sortDir}`;
  const isValidSortKey = sortKey in SORT_LABELS;

  const setSort = useCallback(
    (id: SortOption, desc: boolean) => {
      onSortingChange([{ id, desc }]);
    },
    [onSortingChange]
  );

  const selectedIndustryOptions = useMemo(
    () =>
      selectedIndustries
        .map((id) => industryOptions.find((o) => (o.value as string) === id))
        .filter(Boolean) as DropdownOption[],
    [selectedIndustries, industryOptions]
  );

  return (
    <div className="-mt-2 mb-3 flex w-full min-w-0 max-w-full flex-col gap-2 pb-2 pt-2">
      {/* Search + Filters button row — no horizontal padding; parent provides alignment */}
      <div className="flex w-full min-w-0 gap-2">
        <TextField
          size="small"
          placeholder="Search companies..."
          value={search ?? ""}
          onChange={(e) => onSearchChange(e.target.value)}
          className="min-w-0 flex-1"
          sx={{ "& .MuiOutlinedInput-root": { borderRadius: 2 } }}
          inputProps={{ "aria-label": "Search" }}
        />
        <Button
          variant="outlined"
          onClick={() => setDrawerOpen(true)}
          startIcon={<FilterListIcon />}
          sx={{ borderRadius: 2, flexShrink: 0 }}
          aria-label="Open filters"
        >
          Filters
          {activeFilterCount > 0 && (
            <span className="ml-1 rounded-full bg-brand-500 px-1.5 py-0 text-xs font-semibold text-white">
              {activeFilterCount}
            </span>
          )}
        </Button>
      </div>

      {/* Inline sort on small screens: single select */}
      <FormControl size="small" fullWidth sx={{ maxWidth: 280 }}>
        <InputLabel id="mobile-sort-label">Sort by</InputLabel>
        <Select
          labelId="mobile-sort-label"
          label="Sort by"
          value={isValidSortKey ? sortKey : "created_at-desc"}
          onChange={(e) => {
            const [id, dir] = (e.target.value as string).split("-") as [SortOption, SortDirection];
            setSort(id, dir === "desc");
          }}
          sx={{ borderRadius: 2 }}
        >
          <MenuItem value="created_at-desc">{SORT_LABELS["created_at-desc"]}</MenuItem>
          <MenuItem value="created_at-asc">{SORT_LABELS["created_at-asc"]}</MenuItem>
          <MenuItem value="updated_at-desc">{SORT_LABELS["updated_at-desc"]}</MenuItem>
          <MenuItem value="updated_at-asc">{SORT_LABELS["updated_at-asc"]}</MenuItem>
          <MenuItem value="funding_usd-desc">{SORT_LABELS["funding_usd-desc"]}</MenuItem>
          <MenuItem value="funding_usd-asc">{SORT_LABELS["funding_usd-asc"]}</MenuItem>
        </Select>
      </FormControl>

      <p className="text-xs text-slate-500 dark:text-slate-400">
        {totalCount} companies
      </p>

      <Drawer
        anchor="bottom"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        disableScrollLock
        PaperProps={{
          sx: {
            borderTopLeftRadius: 16,
            borderTopRightRadius: 16,
            maxHeight: "85vh",
            pb: 2,
          },
        }}
      >
        <div className="flex flex-col gap-4 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
              Filters
            </h2>
            <Button onClick={() => setDrawerOpen(false)}>Done</Button>
          </div>

          <FormControl size="small" fullWidth>
            <InputLabel id="drawer-sort-label">Sort by</InputLabel>
            <Select
              labelId="drawer-sort-label"
              label="Sort by"
              value={isValidSortKey ? sortKey : "created_at-desc"}
              onChange={(e) => {
                const [id, dir] = (e.target.value as string).split("-") as [SortOption, SortDirection];
                setSort(id, dir === "desc");
              }}
              sx={{ borderRadius: 2 }}
            >
              <MenuItem value="created_at-desc">{SORT_LABELS["created_at-desc"]}</MenuItem>
              <MenuItem value="created_at-asc">{SORT_LABELS["created_at-asc"]}</MenuItem>
              <MenuItem value="updated_at-desc">{SORT_LABELS["updated_at-desc"]}</MenuItem>
              <MenuItem value="updated_at-asc">{SORT_LABELS["updated_at-asc"]}</MenuItem>
              <MenuItem value="funding_usd-desc">{SORT_LABELS["funding_usd-desc"]}</MenuItem>
              <MenuItem value="funding_usd-asc">{SORT_LABELS["funding_usd-asc"]}</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" fullWidth>
            <InputLabel id="drawer-industry-sort-label">Industry list order</InputLabel>
            <Select
              labelId="drawer-industry-sort-label"
              label="Industry list order"
              value={industryOptionSortBy}
              onChange={(e) =>
                onIndustryOptionSortByChange(e.target.value as IndustryOptionSortBy)
              }
              sx={{ borderRadius: 2 }}
            >
              <MenuItem value="default">Default</MenuItem>
              <MenuItem value="alphabetical">Alphabetical</MenuItem>
              <MenuItem value="industryCount">Industry Count</MenuItem>
            </Select>
          </FormControl>

          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Funding USD
            </span>
            <div className="flex min-w-0 gap-2">
              <TextField
                size="small"
                type="number"
                label="Min"
                placeholder="Min"
                value={fundingUsdMin ?? ""}
                onChange={(e) => {
                  const v = e.target.value;
                  const n = v === "" ? undefined : Number(v);
                  onFundingUsdChange(Number.isFinite(n) ? n : undefined, fundingUsdMax);
                }}
                inputProps={{ min: 0, step: 1000 }}
                sx={{
                  flex: 1,
                  minWidth: 112,
                  "& .MuiOutlinedInput-root": { borderRadius: 2 },
                }}
              />
              <TextField
                size="small"
                type="number"
                label="Max"
                placeholder="Max"
                value={fundingUsdMax ?? ""}
                onChange={(e) => {
                  const v = e.target.value;
                  const n = v === "" ? undefined : Number(v);
                  onFundingUsdChange(fundingUsdMin, Number.isFinite(n) ? n : undefined);
                }}
                inputProps={{ min: 0, step: 1000 }}
                sx={{
                  flex: 1,
                  minWidth: 112,
                  "& .MuiOutlinedInput-root": { borderRadius: 2 },
                }}
              />
            </div>
          </div>

          <Autocomplete<DropdownOption, true>
            multiple
            size="small"
            options={industryOptions}
            value={selectedIndustryOptions}
            onChange={(_, newValue) =>
              onIndustriesChange(newValue.map((o) => o.value as string))
            }
            getOptionLabel={(option) =>
              typeof option === "string" ? option : option.label ?? ""
            }
            isOptionEqualToValue={(option, value) =>
              (option.value as string) === (value?.value as string)
            }
            renderInput={(params) => (
              <TextField {...params} label="Industries" placeholder="Select industries" />
            )}
            sx={{ "& .MuiOutlinedInput-root": { borderRadius: 2 } }}
            chipProps={{ size: "small" }}
            limitTags={3}
          />
        </div>
      </Drawer>
    </div>
  );
}
