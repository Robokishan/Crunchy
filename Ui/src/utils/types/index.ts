export interface CompayDetail {
    _id: string;
    name: string;
    funding: string;
    funding_usd: number;
    website: string;
    crunchbase_url: string;
    tracxn_url?: string;
    logo: string;
    founders: string[];
    similar_companies: string[];
    description: string;
    created_at: Date;
    updated_at: Date;
    long_description: string;
    acquired: null;
    industries: string[];
    founded: string;
    lastfunding: string;
    stocksymbol: string;
}

export interface IndustryFundingChartRow {
    industry: string;
    company_count: number;
    median_funding_usd: number;
    total_funding_usd: number;
}

export interface IndustryOverviewCountRow {
    industry: string;
    company_count: number;
}

export interface IndustryOverviewFundingRow {
    industry: string;
    company_count: number;
    total_funding_usd: number;
}

export interface IndustryOverviewAnalyticsResponse {
    topN: number;
    summary: {
        total_companies: number;
        funded_companies: number;
        total_funding_usd: number;
        total_industries: number;
    };
    industry_by_company_count: IndustryOverviewCountRow[];
    industry_by_total_funding: IndustryOverviewFundingRow[];
}

export interface IndustryFundingAnalyticsResponse {
    metric: "median_funding_usd" | "total_funding_usd";
    results: IndustryFundingChartRow[];
    applied_filters: {
        search: string;
        fundingMin: number | null;
        fundingMax: number | null;
        analyticsMode: "legacy" | "industry_total";
        industryGroupOperator: "any" | "all";
        industryGroups: IndustryQueryGroupPayload[];
        excludedIndustries: string[];
    };
}

export interface IndustryQueryGroupPayload {
    operator: "any" | "all";
    industries: string[];
}

export interface IndustryQueryGroup extends IndustryQueryGroupPayload {
    id: string;
}

export interface IndustryFundingFilterState {
    search: string;
    fundingMin?: number;
    fundingMax?: number;
    analyticsMode: "legacy" | "industry_total";
    industryGroupOperator: "any" | "all";
    industryGroups: IndustryQueryGroup[];
    excludedIndustries: string[];
}
