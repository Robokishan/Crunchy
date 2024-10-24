/* eslint-disable @typescript-eslint/no-misused-promises */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
import { CompanyDetails } from "~/components/Companies";
import crunchyClient from "~/utils/crunchyClient";
import { GetServerSideProps } from "next";
import type { InferGetServerSidePropsType } from "next";
import { Industry } from "~/hooks/industryList";

export const getServerSideProps = async () => {
  try {
    const { data: industries } = await crunchyClient.get<Industry[]>(
      "/public/industries"
    );
    return {
      props: {
        industries,
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

export default function Home({
  industries,
}: InferGetServerSidePropsType<typeof getServerSideProps>) {
  return <CompanyDetails industries={industries ?? []} />;
}
