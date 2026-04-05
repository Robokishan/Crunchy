import { Link, useLocation } from "react-router-dom";

const items = [
  { label: "Overview", href: "/analytics/overview" },
  { label: "Explorer", href: "/analytics/industry-funding" },
];

export function AnalyticsNav() {
  const location = useLocation();

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      {items.map((item) => {
        const active = location.pathname === item.href;
        return (
          <Link
            key={item.href}
            to={item.href}
            className={`inline-flex items-center rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
              active
                ? "border-brand-500 bg-brand-500/10 text-brand-300"
                : "border-slate-600 text-slate-300 hover:border-slate-500 hover:bg-slate-800/60"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </div>
  );
}
