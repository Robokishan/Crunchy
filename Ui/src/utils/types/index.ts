export interface CompayDetail {
    _id: string;
    name: string;
    funding: string;
    funding_usd: number;
    website: string;
    crunchbase_url: string;
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
