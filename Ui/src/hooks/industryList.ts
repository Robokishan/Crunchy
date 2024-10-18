import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import crunchyClient from "~/utils/crunchyClient";

const fetchIndustries = async (
  selectedIndustries: string[]
): Promise<string[]> => {
  const response = await crunchyClient.get<string[]>(`/public/industries`, {
    params: {
      selected: selectedIndustries,
    },
  });
  return response.data;
};

const useIndustryList = (
  defaultIndustry: string[],
  selectedIndustry?: string[]
) => {
  const [industry, setIndustry] = useState<string[]>([]);
  const { data: industries, isLoading } = useQuery<string[], Error>({
    queryKey: ["industries", selectedIndustry],
    queryFn: () => fetchIndustries(selectedIndustry ?? []),
    enabled: selectedIndustry && selectedIndustry.length > 0,
  });

  useEffect(() => {
    if (isLoading === true) return;
    if (
      selectedIndustry &&
      selectedIndustry.length > 0 &&
      industries &&
      industries.length > 0
    ) {
      setIndustry(industries);
    } else {
      setIndustry(defaultIndustry);
    }
  }, [selectedIndustry, defaultIndustry, industries, isLoading]);

  return industry;
};

export default useIndustryList;
