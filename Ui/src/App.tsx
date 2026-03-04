import { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { ThemeContextProvider } from "~/contexts/ThemeContext";
import { HeaderScrollProvider } from "~/contexts/HeaderScrollContext";
import Shield from "~/components/Shield";
import Header from "~/components/Header";
import { CompanyDetails } from "~/components/Companies";
import { Settings } from "~/components/Settings";
import { Connection } from "~/components/Connection";
import { useQuery } from "@tanstack/react-query";
import crunchyClient from "~/utils/crunchyClient";
import type { Industry } from "~/hooks/industryList";

function Home() {
  const { data: industries = [] } = useQuery({
    queryKey: ["industries-initial"],
    queryFn: async () => {
      const { data } = await crunchyClient.get<Industry[]>("/public/industries");
      return data;
    },
  });

  return <CompanyDetails industries={industries} />;
}

export default function App() {
  useEffect(() => {
    document.body.classList.add("app-loaded");
  }, []);

  return (
    <ThemeContextProvider>
      <HeaderScrollProvider>
        <Shield>
          <div className="flex min-h-screen w-full min-w-0 max-w-[100vw] flex-col overflow-x-clip">
            <Header />
            <main className="w-full min-w-0 max-w-[100vw] flex-1 overflow-x-clip px-2 sm:px-4">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/connections" element={<Connection />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </Shield>
      </HeaderScrollProvider>
    </ThemeContextProvider>
  );
}
