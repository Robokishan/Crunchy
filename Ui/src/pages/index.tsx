/* eslint-disable @typescript-eslint/no-misused-promises */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
import type {
  InferGetServerSidePropsType
} from "next";
import { useCallback, useEffect, useState } from "react";
import { CompanyDetails } from "~/components/Companies";
import crunchyClient from "~/utils/crunchyClient";

export const getServerSideProps = async () => {
  try {
    const { data: companiesList } = await crunchyClient.get("/public/comp")
    return {
      props: {
        companiesList,
      },
    };
  } catch (error) {
    console.error("Server side error ", error)
    return {
      props: {
        error: "Something went wrong",
      },
    };
  }
};

const DEFAULT_URL = "/public/comp"

export default function Home({ companiesList }: InferGetServerSidePropsType<typeof getServerSideProps>) {


  const [companies, setCompanies] = useState(companiesList ?? [])

  const [url, setSearchUrl] = useState(DEFAULT_URL)

  const fetchApi = (urlPath: string) => crunchyClient.get(urlPath).then(response => {
    setCompanies(response.data);
  })

  useEffect(() => {
    const timer = setInterval(() => fetchApi(url), 2000)
    return () => clearInterval(timer)
  }, [url])


  const onSearch = useCallback((value: string) => {
    const urlPath = value && value.length > 0 ? DEFAULT_URL + `?search=${value}` : DEFAULT_URL
    setSearchUrl(urlPath)
    fetchApi(urlPath).catch(err => console.error("fetchapi error",err))
  }, [])

  return (
    <>
      <CompanyDetails onSearch={onSearch} companyDetails={companies} />
    </>
  );
}
