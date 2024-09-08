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
      console.log({ sourceType, value, targetType });
      if (sourceType === "" || value == "" || targetType === "") return;
      const urlPath = DEFAULT_URL + `?${sourceType}=${value}&key=${targetType}`;
      setSearchUrl(urlPath);
    },
    []
  );

  return (
    <div className="mb-2 mt-2 rounded-md bg-white p-5 shadow-2xl">
      <div className="flex items-center gap-2">
        <h1 className="mr-5 text-center text-xl text-gray-400">
          Find Connections
        </h1>
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

      <Grid container spacing={2}>

      <Grid item xs={8} md={4}>
      <Grid container spacing={2} alignItems="center">

      <FormControl variant="standard" sx={{ m: 1, minWidth: 120 }}>
        <TypeSelector
          label="Source"
          labelId="source-Label-Type"
          selectId="source-select"
          handleChange={(e :any) => setSourceType(e.target.value)}
        />
      </FormControl>
      <FormControl variant="standard" sx={{ m: 1, minWidth: 120 }}>
        <input
          type="text"
          placeholder="Search"
          onChange={(e) => setSourceValue(e.target.value)}
          className="rounded-l border border-gray-300 bg-gray-200 px-4 py-2 focus:bg-white focus:outline-none"
        />
      </FormControl>
      <FormControl variant="standard" sx={{ m: 1, minWidth: 120 }}>
        <TypeSelector
          label="Target"
          labelId="target-Label-Type"
          selectId="target-select"
          handleChange={(e :any) => setTargetType(e.target.value)}
        />
      </FormControl>
      <button
        onClick={() => onSearch({ sourceType, targetType, value: sourceValue })}
      >
        <ArrowTopRightOnSquareIcon className="h-5 w-5 fill-gray-800" />
      </button>
      </Grid>
      </Grid>
      <Grid item xs={8} md={4}>
        <TextareaAutosize maxRows={100} style={{
          width: "100vh",
          background: "#353B43",
          color: "#F9F9F9",
          fontFamily: "monospace",
        }} value={JSON.stringify(fetchedData, null, 2)} />
        </Grid>
      </Grid>
    </div>
  );
};
