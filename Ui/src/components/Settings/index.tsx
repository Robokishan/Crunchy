import { Button, Grid2 } from "@mui/material";
import Checkbox from "@mui/material/Checkbox";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import useSWR from "swr";
import crunchyClient from "~/utils/crunchyClient";
import Switch from "@mui/material/Switch";
import { TextareaAutosize } from "@mui/material";

const DEFAULT_URL = "/public/settings";

export const Settings = () => {
  const [fetchedData, setData] = useState([]);
  const abortConRef = useRef<AbortController>();
  const [settingsView, setSettingsView] = useState<"text" | "list">("list");

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
    <div className="card-base mx-4 mb-6 mt-6 w-full max-w-6xl sm:mx-6 md:mx-auto">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="page-title">Settings</h1>
        <label className="flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
          <Switch
            checked={settingsView === "list"}
            onChange={() =>
              setSettingsView((prev) => (prev === "list" ? "text" : "list"))
            }
            aria-label="Toggle list or text view"
            size="small"
          />
          <span>{settingsView === "list" ? "List view" : "Text view"}</span>
        </label>
      </div>
      <hr className="my-4 border-0 bg-slate-200 dark:bg-slate-600" style={{ height: 1 }} />
      {isFetching || isLoading ? (
        <p className="text-slate-600 dark:text-slate-300">Loading...</p>
      ) : settingsView === "list" ? (
        <>
          <Grid2 container>
            <Grid2 size={4}>
              <List
                sx={{
                  width: "100%",
                  maxWidth: 360,
                  bgcolor: "background.paper",
                  borderRadius: 2,
                  border: "1px solid",
                  borderColor: "divider",
                }}
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
                        <ListItemText id={labelId} primary={value} sx={{ color: "inherit" }} />
                      </ListItemButton>
                    </ListItem>
                  );
                })}
              </List>
            </Grid2>
            {/* vertical straight line */}

            <Grid2>
              <Button
                variant="contained"
                onClick={() => save()}
                sx={{
                  textTransform: "none",
                  fontWeight: 600,
                  borderRadius: 2,
                  px: 2.5,
                  py: 1.25,
                  boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                }}
              >
                Save
              </Button>
            </Grid2>

            <Grid2 size={4}>
              <List
                sx={{
                  width: "100%",
                  maxWidth: 360,
                  bgcolor: "background.paper",
                  borderRadius: 2,
                  border: "1px solid",
                  borderColor: "divider",
                }}
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
                        <ListItemText id={labelId} primary={value} sx={{ color: "inherit" }} />
                      </ListItemButton>
                    </ListItem>
                  );
                })}
              </List>
            </Grid2>
          </Grid2>
        </>
      ) : settingsView === "text" ? (
        <Grid2 container spacing={3}>
          <Grid2 size={6}>
            <TextareaAutosize
              maxRows={50}
              name="name"
              placeholder="Industries JSON"
              value={JSON.stringify(data?.data.industries, null, 2)}
              className="input-base min-h-[200px] font-mono text-sm"
            />
          </Grid2>
          <Grid2 size={6}>
            <TextareaAutosize
              maxRows={50}
              name="name"
              placeholder="Interested industries JSON"
              value={JSON.stringify(data?.data.interested_industries, null, 2)}
              className="input-base min-h-[200px] font-mono text-sm"
            />
          </Grid2>
        </Grid2>
      ) : null}
    </div>
  );
};
