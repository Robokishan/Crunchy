import { XMarkIcon } from "@heroicons/react/24/outline";
import axios from "axios";
import Image from "next/image";
import { useEffect, useState } from "react";
import Modal from "react-modal";
import { toast } from "react-toastify";

type Props = {
  setModal: (openModal: boolean) => void;
  modalIsOpen: boolean;
  modalData: any;
};

export interface CompanyDetails {
  founders: string[];
  tags: string[];
  name: string;
  funding: string;
  website: string;
  crunchbaseUrl: string;
  iconUrl: string;
  description: string;
  founded: string;
  lastfunding: string;
  stocksymbol: string;
  acquired: string;
}

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

Modal.setAppElement("#popup");

export default function ExportToNotion({
  setModal,
  modalIsOpen,
  modalData,
}: Props) {
  const [isLoading, setLoader] = useState(false);
  const [notionData, setNotionData] = useState<CompanyDetails>(
    modalData && {
      crunchbaseUrl: modalData.crunchbase_url,
      description: modalData.description,
      founded: modalData.founded,
      founders: modalData.founders,
      funding: modalData.funding,
      iconUrl: modalData.logo,
      lastfunding: modalData.lastfunding,
      name: modalData.name,
      stocksymbol: modalData.stocksymbol,
      tags: modalData.industries,
      website: modalData.website,
      acquired: modalData.acquired,
    }
  );

  useEffect(() => {
    setNotionData({
      crunchbaseUrl: modalData.crunchbase_url,
      description: modalData.description,
      founded: modalData.founded,
      founders: modalData.founders,
      funding: modalData.funding,
      iconUrl: modalData.logo,
      lastfunding: modalData.lastfunding,
      name: modalData.name,
      stocksymbol: modalData.stocksymbol,
      tags: modalData.industries,
      website: modalData.website,
      acquired: modalData.acquired,
    });
  }, [modalData]);

  return (
    <Modal
      isOpen={modalIsOpen}
      onRequestClose={() => setModal(false)}
      style={customStyles}
      contentLabel="Export to Notion Modal"
    >
      <div>
        {/* title */}
        <div className="flex items-center gap-5 ">
          <span>Export To Notion</span>
          <XMarkIcon
            onClick={() => setModal(false)}
            className="ml-auto h-6 w-6 cursor-pointer text-slate-500"
          />
        </div>
        {/* body */}
        <div className="mt-2 grid grid-cols-2 gap-4">
          <input
            name="name"
            placeholder="Name"
            value={notionData?.name}
            className="m-0 rounded-md border border-solid  px-2 py-2 focus:border-sky-500  focus:outline-none"
            onChange={(e) => {
              setNotionData((prev: any) => ({
                ...prev,
                [e.target.name]: e.target.value,
              }));
            }}
          />
          <input
            name="crunchbaseUrl"
            placeholder="Crunchbase URL"
            value={notionData?.crunchbaseUrl}
            className="m-0 rounded-md border border-solid  px-2 py-2 focus:border-sky-500  focus:outline-none"
            onChange={(e) => {
              setNotionData((prev: any) => ({
                ...prev,
                [e.target.name]: e.target.value,
              }));
            }}
          />
          <input
            name="website"
            placeholder="Website"
            value={notionData?.website}
            className="m-0 rounded-md border border-solid  px-2 py-2 focus:border-sky-500  focus:outline-none"
            onChange={(e) => {
              setNotionData((prev: any) => ({
                ...prev,
                [e.target.name]: e.target.value,
              }));
            }}
          />
          <input
            name="funding"
            placeholder="Funding"
            value={notionData?.funding}
            className="m-0 rounded-md border border-solid  px-2 py-2 focus:border-sky-500  focus:outline-none"
            onChange={(e) => {
              setNotionData((prev: any) => ({
                ...prev,
                [e.target.name]: e.target.value,
              }));
            }}
          />
          <input
            name="iconUrl"
            placeholder="Logo"
            className="m-0 rounded-md border border-solid  px-2 py-2 focus:border-sky-500  focus:outline-none"
            value={notionData?.iconUrl}
            onChange={(e) => {
              setNotionData((prev: any) => ({
                ...prev,
                [e.target.name]: e.target.value,
              }));
            }}
          />
          <Image
            src={notionData?.iconUrl}
            alt="company-icon"
            width={40}
            height={40}
          />
          <input
            name="acquired"
            placeholder="Acquired"
            className="m-0 rounded-md border border-solid  px-2 py-2 focus:border-sky-500  focus:outline-none"
            value={notionData?.acquired}
            onChange={(e) => {
              setNotionData((prev: any) => ({
                ...prev,
                [e.target.name]: e.target.value,
              }));
            }}
          />
          <input
            name="description"
            placeholder="Description"
            className="m-0 rounded-md border border-solid  px-2 py-2 focus:border-sky-500  focus:outline-none"
            value={notionData?.description}
            onChange={(e) => {
              setNotionData((prev: any) => ({
                ...prev,
                [e.target.name]: e.target.value,
              }));
            }}
          />
          <input
            name="lastfunding"
            placeholder="Last Fund"
            className="m-0 rounded-md border border-solid  px-2 py-2 focus:border-sky-500  focus:outline-none"
            value={notionData?.lastfunding}
            onChange={(e) => {
              setNotionData((prev: any) => ({
                ...prev,
                [e.target.name]: e.target.value,
              }));
            }}
          />
        </div>
        <div className="mb-2 mt-8 flex gap-3">
          <button
            className="text-slate ml-auto cursor-pointer rounded-md bg-slate-100 p-2 text-slate-600 shadow-xl shadow-gray-200"
            onClick={() => setModal(false)}
          >
            Cancel
          </button>
          <button
            disabled={isLoading}
            className={`text-slate first-letter: inline-flex cursor-pointer items-center rounded-md bg-slate-800 
            px-3
            py-2
            text-slate-300
            shadow-xl
            shadow-gray-200
            ${isLoading && "opacity-50"}`}
            onClick={() => {
              setLoader(true);
              axios
                .post("/api/notion/export", notionData)
                .then(() => {
                  toast(`Export Done ${notionData.name}`, {
                    type: "success",
                  });
                  setModal(false);
                })
                .catch((err) =>
                  toast("Export Failed", {
                    data: err,
                    type: "error",
                  })
                )
                .finally(() => setLoader(false));
            }}
          >
            {isLoading && <Loader />}
            Export to Notion
          </button>
        </div>
      </div>
    </Modal>
  );
}

function Loader() {
  return (
    <svg
      aria-hidden="true"
      role="status"
      className="mr-2 inline h-4 w-4 animate-spin text-gray-800 "
      viewBox="0 0 100 101"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
        fill="currentColor"
      />
      <path
        d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
        fill="white"
      />
    </svg>
  );
}
