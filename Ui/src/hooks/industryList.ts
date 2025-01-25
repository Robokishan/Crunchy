import { useQuery } from "@tanstack/react-query";
import { DropdownOption } from "material-react-table";
import { useEffect, useMemo, useState } from "react";
import crunchyClient from "~/utils/crunchyClient";

export type Industry = {
  industry: string;
  count: number;
};

const fetchIndustries = async (
  selectedIndustries: string[],
  sortBy?: string
): Promise<Industry[]> => {
  const response = await crunchyClient.get<Industry[]>(`/public/industries`, {
    params: {
      selected: selectedIndustries,
      sortBy: sortBy,
    },
  });
  return response.data;
};

const useIndustryList = (
  defaultIndustry: Industry[],
  selectedIndustry?: string[],
  industrySortBy?: string
): DropdownOption[] => {
  const [industry, setIndustry] = useState<Industry[]>([]);
  const { data: industries, isLoading } = useQuery<Industry[], Error>({
    queryKey: ["industries", selectedIndustry, industrySortBy],
    queryFn: () => fetchIndustries(selectedIndustry ?? [], industrySortBy),
    enabled: Boolean(selectedIndustry && selectedIndustry.length > 0),
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

  const industryOptions = useMemo(() => {
    return industry.map((industry) => ({
      label: `${industry.industry} (${industry.count})`,
      value: industry.industry,
    }));
  }, [industry]);

  return industryOptions;
};

export default useIndustryList;
