import { Divider, Typography } from "@mui/material";
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
    <div className="flex gap-1">
      <Typography component="span" color="error">
        Priority:
      </Typography>
      <Typography component="span" color="error">
        {data?.data.priority ?? "-"}
      </Typography>
      <Divider
        orientation="vertical"
        flexItem
        sx={{
          color: "black",
          borderRightWidth: 2,
          marginX: "3px",
        }}
      />
      <Typography component="span" color="warning">
        Normal:
      </Typography>
      <Typography component="span" color="warning">
        {data?.data.normal ?? "-"}
      </Typography>
    </div>
  );
};
