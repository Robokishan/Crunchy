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
        boxShadow: "0px 6px 28px 4px rgba(90, 106, 157, 0.2)",
        width: "30%",
        border: "0px",
        minWidth: "400px",
        top: "50%",
        left: "50%",
        right: "auto",
        bottom: "auto",
        maxHeight: "calc(100vh - 15rem)",
        marginRight: "-50%",
        transform: "translate(-50%, -50%)",
        borderRadius: "16px",
        padding: "40px 44px 18px",
        backgroundColor: isDark ? "#1f2937" : "#fff",
        color: isDark ? "#e5e7eb" : "#111827",
      } as React.CSSProperties,
      overlay: {
        zIndex: 50,
        position: "fixed" as const,
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: isDark ? "rgba(0,0,0,0.75)" : "#E5E5E580",
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
        {/* title */}
        <div className="flex items-center gap-5 ">
          <span className="text-lg font-medium">Create Crawl</span>
          <XMarkIcon
            onClick={() => setModal(false)}
            className="ml-auto h-6 w-6 cursor-pointer text-slate-500 hover:text-slate-700 dark:text-gray-400 dark:hover:text-gray-200"
          />
        </div>
        {/* body */}
        <div className="mt-2 w-full">
          <TextareaAutosize
            maxRows={15}
            minRows={10}
            name="name"
            placeholder="Name"
            value={crawlPostData}
            style={{
              padding: "10px",
              width: "100%",
              background: isDark ? "#374151" : "#f3f4f6",
              color: isDark ? "#e5e7eb" : "#111827",
              fontFamily: "monospace",
              border: "1px solid " + (isDark ? "#4b5563" : "#d1d5db"),
              borderRadius: "8px",
            }}
            onChange={handleChange}
          />
        </div>
        {error && <div className="mt-1 text-red-500 dark:text-red-400">{error}</div>}
        <div className="mb-2 mt-8 flex gap-3">
          <button
            className="ml-auto cursor-pointer rounded-md p-2 shadow-xl bg-slate-100 text-slate-600 shadow-gray-200 hover:bg-slate-200 dark:bg-gray-600 dark:text-gray-200 dark:shadow-gray-900 dark:hover:bg-gray-500"
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
