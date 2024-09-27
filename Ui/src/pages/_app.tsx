import { type AppType } from "next/dist/shared/lib/utils";
import Shield from "~/components/Shield";
import Header from "~/components/Header";
import "~/styles/globals.css";

const MyApp: AppType = ({ Component, pageProps }) => {
  return (
    <Shield>
      <Header />
      <Component {...pageProps} />
    </Shield>
  );
};

export default MyApp;
