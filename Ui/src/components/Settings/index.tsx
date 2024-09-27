import { Button, Grid2 } from "@mui/material";
import Checkbox from "@mui/material/Checkbox";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import { useEffect, useRef, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import useSWR from "swr";
import crunchyClient from "~/utils/crunchyClient";

const DEFAULT_URL = "/public/settings";

export const Settings = () => {
  const [fetchedData, setData] = useState([]);
  const abortConRef = useRef<AbortController>();

  const [url, setSearchUrl] = useState(DEFAULT_URL);
  const {
    data,
    isValidating: isLoading,
    isLoading: isFetching,
    mutate,
  } = useSWR(url, fetchApi, {
    refreshInterval: 0, // Disable interval call
    shouldRetryOnError: false, // Disable automatic retries on error
    dedupingInterval: Infinity, // Disable deduping of requests
    revalidateOnFocus: false, // Disable revalidation on focus
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

  const [checked, setChecked] = useState<string[]>([]);

  const handleToggle = (value: string) => () => {
    const currentIndex = checked.indexOf(value);
    const newChecked = [...checked];

    if (currentIndex === -1) {
      newChecked.push(value);
    } else {
      newChecked.splice(currentIndex, 1);
    }

    setChecked(newChecked);
  };

  const save = async () => {
    const settingsPromise = crunchyClient.post("/public/settings", {
      industry: checked,
    });
    toast.promise(settingsPromise, {
      loading: "Saving",
      success: "Saved",
      error: "Something went wrong",
    });
    setTimeout(mutate, 2000);
  };

  useEffect(() => {
    setChecked(data?.data.interested_industries ?? []);
  }, [data?.data.interested_industries]);

  return (
    <div className="mb-2 mt-2 rounded-md bg-white p-5 shadow-2xl">
      <Toaster />
      <div className="flex items-center gap-2">
        <h1 className="mr-5 text-center text-xl text-gray-400">Settings</h1>
      </div>
      <hr className="my-3 h-px border-0 bg-gray-200 " />
      {isFetching || isLoading ? (
        <h1>Loading...</h1>
      ) : (
        <Grid2 container>
          <Grid2>
            <List
              sx={{ width: "100%", maxWidth: 360, bgcolor: "background.paper" }}
            >
              {data?.data.industries.map((value: any) => {
                const labelId = `checkbox-list-label-${value}`;

                return (
                  <ListItem key={value} disablePadding>
                    <ListItemButton
                      role={undefined}
                      onClick={handleToggle(value)}
                      dense
                    >
                      <ListItemIcon>
                        <Checkbox
                          edge="start"
                          checked={checked.includes(value)}
                          tabIndex={-1}
                          disableRipple
                          inputProps={{ "aria-labelledby": labelId }}
                        />
                      </ListItemIcon>
                      <ListItemText id={labelId} primary={value} />
                    </ListItemButton>
                  </ListItem>
                );
              })}
            </List>
          </Grid2>
          {/* vertical straight line */}

          <Grid2>
            <Button
              sx={{
                color: "blue",
                marginRight: "10px",
              }}
              variant="contained"
              onClick={() => save()}
            >
              <h1>Save</h1>
            </Button>
          </Grid2>

          <Grid2>
            <List
              sx={{ width: "100%", maxWidth: 360, bgcolor: "background.paper" }}
            >
              {data?.data.interested_industries.map((value: any) => {
                const labelId = `checkbox-list-label-${value}`;

                return (
                  <ListItem key={value} disablePadding>
                    <ListItemButton
                      role={undefined}
                      onClick={handleToggle(value)}
                      dense
                    >
                      <ListItemIcon>
                        <Checkbox
                          edge="start"
                          checked={checked.includes(value)}
                          tabIndex={-1}
                          disableRipple
                          inputProps={{ "aria-labelledby": labelId }}
                        />
                      </ListItemIcon>
                      <ListItemText id={labelId} primary={value} />
                    </ListItemButton>
                  </ListItem>
                );
              })}
            </List>
          </Grid2>
        </Grid2>
      )}
    </div>
  );
};
