import { XMarkIcon } from "@heroicons/react/24/outline";
import { LoadingButton } from "@mui/lab";
import { TextareaAutosize } from "@mui/material";
import { useState } from "react";
import toast from "react-hot-toast";
import Modal from "react-modal";
import { isUrl } from "~/utils";
import crunchyClient from "~/utils/crunchyClient";

type Props = {
  setModal: (openModal: boolean) => void;
  modalIsOpen: boolean;
};

const customStyles = {
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
  },
  overlay: {
    zIndex: 50,
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "#E5E5E580",
  },
} as const;

Modal.setAppElement("#createcrawl");

export default function CreateCrawl({ setModal, modalIsOpen }: Props) {
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
          <span>Create Crawl</span>
          <XMarkIcon
            onClick={() => setModal(false)}
            className="ml-auto h-6 w-6 cursor-pointer text-slate-500"
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
              background: "#353B43",
              color: "#F9F9F9",
              fontFamily: "monospace",
            }}
            onChange={handleChange}
          />
        </div>
        {error && <div className="text-red-500">{error}</div>}
        <div className="mb-2 mt-8 flex gap-3">
          <button
            className="text-slate ml-auto cursor-pointer rounded-md bg-slate-100 p-2 text-slate-600 shadow-xl shadow-gray-200"
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
