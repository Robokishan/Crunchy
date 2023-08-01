import { type AppType } from "next/dist/shared/lib/utils";
import Shield from "~/components/Shield";
import "~/styles/globals.css";

const MyApp: AppType = ({ Component, pageProps }) => {
  return (
    <Shield>
      <Component {...pageProps} />
    </Shield>
  );
};

export default MyApp;
