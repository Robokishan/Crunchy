import { FormControl, Grid, TextareaAutosize } from "@mui/material";
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
    <div className="card-base mx-4 mb-6 mt-6 w-full max-w-6xl sm:mx-6 md:mx-auto">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="page-title">Find Connections</h1>
        {isLoading && (
          <span className="relative flex h-3 w-3" aria-hidden>
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-brand-500" />
          </span>
        )}
      </div>
      <hr className="my-4 border-0 bg-slate-200 dark:bg-slate-600" style={{ height: 1 }} />

      <Grid container spacing={3}>
        <Grid item xs={12} md={5}>
          <div className="flex flex-wrap items-end gap-3">
            <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
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
              className="input-base max-w-[200px]"
            />
            <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
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
              className="inline-flex h-10 w-10 items-center justify-center rounded-input border border-slate-300 bg-white text-slate-600 shadow-sm transition-colors hover:bg-slate-50 focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
              aria-label="Search connections"
            >
              <ArrowTopRightOnSquareIcon className="h-5 w-5" />
            </button>
          </div>
        </Grid>
        <Grid item xs={12} md={7}>
          <TextareaAutosize
            maxRows={100}
            value={JSON.stringify(fetchedData, null, 2)}
            className="input-base min-h-[280px] w-full font-mono text-sm"
          />
        </Grid>
      </Grid>
    </div>
  );
};
