import { useRef, useState } from "react";
import useSWR from "swr";
import crunchyClient from "~/utils/crunchyClient";

const DEFAULT_URL = "/public/pending";

export const Pending = () => {
  const abortConRef = useRef<AbortController>();
  const [url, setSearchUrl] = useState(DEFAULT_URL);
  const { data } = useSWR(url, fetchApi, {
    refreshInterval: 2,
  });

  async function fetchApi(urlPath: string) {
    if (abortConRef.current) abortConRef.current.abort();
    abortConRef.current = new AbortController();
    const response = await crunchyClient.get(urlPath, {
      signal: abortConRef.current.signal,
    });
    return response;
  }

  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      <span className="rounded-full bg-red-100 px-2.5 py-0.5 font-medium text-red-800 dark:bg-red-900/40 dark:text-red-300">
        Crunchbase: <strong>{data?.data.crunchbase ?? "-"}</strong>
      </span>
      <span className="rounded-full bg-amber-100 px-2.5 py-0.5 font-medium text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
        Tracxn: <strong>{data?.data.tracxn ?? "-"}</strong>
      </span>
    </div>
  );
};
