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
}

export interface IndustryFundingAnalyticsResponse {
    metric: "median_funding_usd";
    results: IndustryFundingChartRow[];
    applied_filters: {
        search: string;
        fundingMin: number | null;
        fundingMax: number | null;
        industryMode: "any" | "all";
        industries: string[];
    };
}

export interface IndustryFundingFilterState {
    search: string;
    fundingMin?: number;
    fundingMax?: number;
    industryMode: "any" | "all";
    industries: string[];
}
