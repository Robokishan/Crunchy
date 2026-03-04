import { XMarkIcon } from "@heroicons/react/24/outline";
import { LoadingButton } from "@mui/lab";
import { TextareaAutosize } from "@mui/material";
import { useMemo, useState } from "react";
import toast from "react-hot-toast";
import Modal from "react-modal";
import { useThemeMode } from "~/contexts/ThemeContext";
import { isUrl } from "~/utils";
import crunchyClient from "~/utils/crunchyClient";

type Props = {
  setModal: (openModal: boolean) => void;
  modalIsOpen: boolean;
};

Modal.setAppElement("#createcrawl");

export default function CreateCrawl({ setModal, modalIsOpen }: Props) {
  const { effectiveTheme } = useThemeMode();
  const isDark = effectiveTheme === "dark";

  const customStyles = useMemo(
    () => ({
      content: {
        boxShadow: isDark
          ? "0 25px 50px -12px rgb(0 0 0 / 0.5), 0 0 0 1px rgb(255 255 255 / 0.06)"
          : "0 25px 50px -12px rgb(0 0 0 / 0.15), 0 0 0 1px rgb(0 0 0 / 0.05)",
        width: "30%",
        border: "none",
        minWidth: "400px",
        maxWidth: "520px",
        top: "50%",
        left: "50%",
        right: "auto",
        bottom: "auto",
        maxHeight: "calc(100vh - 8rem)",
        overflow: "auto",
        marginRight: "-50%",
        transform: "translate(-50%, -50%)",
        borderRadius: "16px",
        padding: "32px 40px 24px",
        backgroundColor: isDark ? "#1e293b" : "#fff",
        color: isDark ? "#e2e8f0" : "#0f172a",
      } as React.CSSProperties,
      overlay: {
        zIndex: 50,
        position: "fixed" as const,
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: isDark ? "rgba(15,23,42,0.82)" : "rgba(15,23,42,0.4)",
        backdropFilter: "blur(4px)",
      } as React.CSSProperties,
    }),
    [isDark]
  );

  const [isLoading, setLoading] = useState(false);
  const [createCrawlStatus, setCreateCrawlStatus] = useState<
    "init" | "done" | "error"
  >("init");
  const [crawlPostData, setCrawlData] = useState<string>();
  const [error, setError] = useState<string>();

  function handleClick() {
    const inValidUrls = crawlPostData?.split("\n").filter((x) => !isUrl(x));
    const _crawlPostData = crawlPostData?.split("\n").filter((x) => isUrl(x));
    if (inValidUrls && inValidUrls.length > 0) {
      setError("Invalid URLs");
      return;
    }

    setLoading(true);
    const postData = {
      url: _crawlPostData,
    };

    const retryPromise = crunchyClient.post("/api/crawl/create", postData);
    toast.promise(retryPromise, {
      loading: "Pushing to queue",
      success: "Pushed to queue",
      error: "Error pushing to queue",
    });
    retryPromise
      .then(() => {
        setCreateCrawlStatus("done");
        setError("");
      })
      .catch((err) => {
        setCreateCrawlStatus("error");
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const input = e.target.value;
    setCrawlData(input);
    setCreateCrawlStatus("init");
  };

  return (
    <Modal
      isOpen={modalIsOpen}
      onRequestClose={() => setModal(false)}
      style={customStyles}
      contentLabel="Create Crawl"
    >
      <div>
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold tracking-tight">Create Crawl</h2>
          <button
            type="button"
            onClick={() => setModal(false)}
            className="ml-auto rounded-input p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 focus-visible:ring-2 focus-visible:ring-brand-500 dark:text-slate-400 dark:hover:bg-slate-600 dark:hover:text-slate-200"
            aria-label="Close"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>
        <div className="mt-4 w-full">
          <TextareaAutosize
            maxRows={10}
            minRows={4}
            name="name"
            placeholder="Paste URLs (one per line)"
            value={crawlPostData}
            className="input-base min-h-[100px] w-full max-h-[240px] overflow-y-auto font-mono text-sm resize-y"
            onChange={handleChange}
          />
        </div>
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400" role="alert">
            {error}
          </p>
        )}
        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setModal(false)}
          >
            Cancel
          </button>
          <LoadingButton
            size="small"
            onClick={handleClick}
            disabled={createCrawlStatus === "done"}
            loading={isLoading}
            loadingIndicator="Pushing.."
            color={
              createCrawlStatus === "done"
                ? "success"
                : createCrawlStatus === "error"
                ? "error"
                : "primary"
            }
            variant="outlined"
          >
            {createCrawlStatus === "init"
              ? "Create Crawl"
              : createCrawlStatus === "done"
              ? "Created🔥"
              : "Error!"}
          </LoadingButton>
        </div>
      </div>
    </Modal>
  );
}
