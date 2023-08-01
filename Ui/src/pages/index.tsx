/* eslint-disable @typescript-eslint/no-misused-promises */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
import type { InferGetServerSidePropsType } from "next";
import { useCallback, useEffect, useRef, useState } from "react";
import useSWR from "swr";
import { CompanyDetails } from "~/components/Companies";
import crunchyClient from "~/utils/crunchyClient";

export const getServerSideProps = async () => {
  try {
    const { data: companiesList } = await crunchyClient.get("/public/comp");
    return {
      props: {
        companiesList,
      },
    };
  } catch (error) {
    console.error("Server side error ", error);
    return {
      props: {
        error: "Something went wrong",
      },
    };
  }
};

const DEFAULT_URL = "/public/comp";

export default function Home({
  companiesList,
}: InferGetServerSidePropsType<typeof getServerSideProps>) {
  const [companies, setCompanies] = useState(companiesList ?? []);

  const abortConRef = useRef<AbortController>();

  const [url, setSearchUrl] = useState(DEFAULT_URL);
  const {
    data,
    error,
    isValidating: isLoading,
  } = useSWR(url, fetchApi, {
    refreshInterval: 2000,
  });

  async function fetchApi(urlPath: string) {
    if (abortConRef.current) abortConRef.current.abort();
    abortConRef.current = new AbortController();
    const response = await crunchyClient.get(urlPath, {
      signal: abortConRef.current.signal,
    });
    setCompanies(response.data);
    return response;
  }

  const onSearch = useCallback((value: string) => {
    const urlPath =
      value && value.length > 0
        ? DEFAULT_URL + `?search=${value}`
        : DEFAULT_URL;
    setSearchUrl(urlPath);
  }, []);

  return (
    <>
      <CompanyDetails
        isLoading={isLoading}
        onSearch={onSearch}
        companyDetails={companies}
      />
    </>
  );
}
