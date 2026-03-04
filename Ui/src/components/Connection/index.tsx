import { Box, FormControl, TextareaAutosize } from "@mui/material";
import { useState, useRef, useCallback } from "react";
import useSWR from "swr";
import crunchyClient from "~/utils/crunchyClient";
import TypeSelector from "../TypeSelector";
import { ArrowTopRightOnSquareIcon } from "@heroicons/react/24/solid";

const DEFAULT_URL = "/public/connection";

export const Connection = () => {
  const [fetchedData, setData] = useState([]);
  const abortConRef = useRef<AbortController>();
  const [sourceType, setSourceType] = useState("");
  const [sourceValue, setSourceValue] = useState("");
  const [targetType, setTargetType] = useState("");

  const [url, setSearchUrl] = useState(DEFAULT_URL);
  const {
    data,
    error,
    isValidating: isLoading,
    mutate,
  } = useSWR(url, fetchApi, {
    revalidateOnMount: false,
    refreshInterval: 0, // Disable interval call
    shouldRetryOnError: false, // Disable automatic retries on error
    dedupingInterval: Infinity, // Disable deduping of requests
  });

  async function fetchApi(urlPath: string) {
    if (abortConRef.current) abortConRef.current.abort();
    abortConRef.current = new AbortController();
    const response = await crunchyClient.get(urlPath, {
      signal: abortConRef.current.signal,
    });
    setData(response.data);
    return response;
  }

  const onSearch = useCallback(
    ({
      sourceType,
      value,
      targetType,
    }: {
      sourceType: string;
      value: string;
      targetType: String;
    }) => {
      if (sourceType === "" || value == "" || targetType === "") return;
      const urlPath = DEFAULT_URL + `?${sourceType}=${value}&key=${targetType}`;
      setSearchUrl(urlPath);
    },
    []
  );

  return (
    <div
      className="card-base mb-6 mt-4 w-full max-w-6xl box-border md:mx-auto"
      style={{
        minWidth: 0,
        maxWidth: "min(100%, 72rem)",
        overflowX: "clip",
        boxSizing: "border-box",
        width: "100%",
      }}
    >
      <div className="flex min-w-0 flex-wrap items-center gap-3">
        <h1 className="page-title text-lg sm:text-xl">Find Connections</h1>
        {isLoading && (
          <span className="relative flex h-3 w-3" aria-hidden>
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-brand-500" />
          </span>
        )}
      </div>
      <hr className="my-4 border-0 bg-slate-200 dark:bg-slate-600" style={{ height: 1 }} />

      {/* Stack on narrow screens to prevent overflow; row on wider */}
      <Box
        sx={{
          display: "flex",
          flexDirection: { xs: "column", sm: "row" },
          flexWrap: "wrap",
          alignItems: "flex-end",
          gap: 1.5,
          minWidth: 0,
          width: "100%",
        }}
      >
        <FormControl
          variant="outlined"
          size="small"
          sx={{ minWidth: 0, flex: { xs: "1 1 auto", sm: "1 1 0" }, width: { xs: "100%", sm: "auto" }, maxWidth: "100%" }}
        >
          <TypeSelector
            label="Source"
            labelId="source-Label-Type"
            selectId="source-select"
            handleChange={(e: any) => setSourceType(e.target.value)}
          />
        </FormControl>
        <input
          type="text"
          placeholder="Search"
          value={sourceValue}
          onChange={(e) => setSourceValue(e.target.value)}
          className="input-base min-w-0 max-w-full flex-1 basis-0 shrink box-border"
          style={{ minWidth: 0, width: "100%", maxWidth: "100%" }}
        />
        <FormControl
          variant="outlined"
          size="small"
          sx={{ minWidth: 0, flex: { xs: "1 1 auto", sm: "1 1 0" }, width: { xs: "100%", sm: "auto" }, maxWidth: "100%" }}
        >
          <TypeSelector
            label="Target"
            labelId="target-Label-Type"
            selectId="target-select"
            handleChange={(e: any) => setTargetType(e.target.value)}
          />
        </FormControl>
        <button
          type="button"
          onClick={() =>
            onSearch({ sourceType, targetType, value: sourceValue })
          }
          className="inline-flex h-10 shrink-0 w-10 items-center justify-center rounded-input border border-slate-300 bg-white text-slate-600 shadow-sm transition-colors hover:bg-slate-50 focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
          aria-label="Search connections"
        >
          <ArrowTopRightOnSquareIcon className="h-5 w-5" />
        </button>
      </Box>
      <Box sx={{ minWidth: 0, width: "100%", mt: 2 }}>
        <TextareaAutosize
          maxRows={100}
          value={JSON.stringify(fetchedData, null, 2)}
          className="input-base min-h-[280px] w-full min-w-0 max-w-full font-mono text-sm box-border"
          style={{ boxSizing: "border-box", maxWidth: "100%" }}
        />
      </Box>
    </div>
  );
};
