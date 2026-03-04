import type { ReactNode } from "react";
import { isUrl } from "~/utils";

/** Order: useful info first (left), then metadata / _id / similar_companies (right). */
const USEFUL_FIRST_ORDER: Record<string, number> = {
  name: 0,
  description: 1,
  long_description: 2,
  industries: 3,
  founders: 4,
  founded: 5,
  funding: 6,
  funding_usd: 7,
  lastfunding: 8,
  stocksymbol: 9,
  acquired: 10,
  website: 11,
  crunchbase_url: 12,
  tracxn_url: 13,
  // metadata / less useful — right side
  created_at: 100,
  updated_at: 101,
  _id: 102,
  sources: 103,
  source_priority: 104,
  match_confidence: 105,
  normalized_domain: 106,
  logo: 107,
  similar_companies: 1000,
};

function getDetailSortKey(entry: { key: string; index: number }): number {
  const k = entry.key;
  const order = USEFUL_FIRST_ORDER[k];
  if (order !== undefined) return order;
  // unknown keys from backend: after main useful block, before metadata
  return 50;
}

/** True if this key is "rest" (metadata / _id / similar_companies) for right column. */
export function isMetadataDetailKey(key: string): boolean {
  const order = USEFUL_FIRST_ORDER[key];
  return (order ?? 50) >= 100;
}

function detailFieldCompare(
  a: { key: string; value: unknown; index: number },
  b: { key: string; value: unknown; index: number }
): number {
  return getDetailSortKey(a) - getDetailSortKey(b);
}

export type DetailEntry = { key: string; value: unknown };

/** Returns all company fields: useful info first (left), then metadata / _id / similar_companies (right). */
export function getSortedDetailEntries(
  company: Record<string, unknown>
): DetailEntry[] {
  const entries = Object.entries(company).map(([key, value], index) => ({
    key,
    value,
    index,
  }));
  return entries
    .sort((a, b) => detailFieldCompare(a, b))
    .map(({ key, value }) => ({ key, value }));
}

export function formatDetailValue(value: unknown): ReactNode {
  if (value == null || value === "") return "-";
  if (typeof value === "string") {
    return isUrl(value) ? (
      <a
        href={value}
        target="_blank"
        rel="noopener noreferrer"
        className="link-underline text-brand-600 dark:text-brand-400"
      >
        {value}
      </a>
    ) : (
      value
    );
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return "-";
    return (
      <span className="flex flex-wrap gap-1">
        {value.map((item, idx) =>
          typeof item === "string" && isUrl(item) ? (
            <a
              key={idx}
              href={item}
              target="_blank"
              rel="noopener noreferrer"
              className="link-underline text-brand-600 dark:text-brand-400"
            >
              {item}
            </a>
          ) : (
            <span
              key={idx}
              className="rounded-full bg-slate-200/80 px-2 py-0.5 text-xs dark:bg-slate-600/80"
            >
              {String(item)}
            </span>
          )
        )}
      </span>
    );
  }
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

/** Human-friendly label for a detail key (e.g. funding_usd → Funding USD). */
export function detailKeyToLabel(key: string): string {
  if (key === "_id") return "Id";
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
