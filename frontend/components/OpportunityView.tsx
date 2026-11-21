"use client";

import { useEffect, useState } from "react";
import { getOpportunities, updateOpportunityStatus } from "@/lib/api";
import type { OpportunityItem } from "@/lib/types";

const TYPE_ICONS: Record<string, string> = {
  contest: "🏆",
  internship: "💼",
  scholarship: "🎓",
  project: "🚀",
};

const STATUS_OPTIONS = ["new", "saved", "applied", "interviewing", "accepted"];

export default function OpportunityView() {
  const [items, setItems] = useState<OpportunityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getOpportunities()
      .then((data) => setItems(data))
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, []);

  const handleStatusChange = async (item: OpportunityItem, newStatus: string) => {
    try {
      await updateOpportunityStatus({
        source: item.source,
        title: item.title,
        due: item.due,
        kind: item.kind,
        otype: item.type,
        status: newStatus,
      });
      setItems((prev) =>
        prev.map((it) => (it.key === item.key ? { ...it, status: newStatus } : it))
      );
    } catch (e) {
      alert(`Could not update status: ${(e as Error).message}`);
    }
  };

  const filtered = items.filter(
    (it) => filterType === "all" || it.type.toLowerCase() === filterType
  );

  if (loading) {
    return (
      <div className="schedule-loading">
        <div className="kairo-spinner" />
        <p className="muted small">Scanning student opportunity horizon…</p>
      </div>
    );
  }

  if (error) {
    return <div className="alert">Could not load opportunities: {error}</div>;
  }

  return (
    <div className="opportunity-container">
      <div className="opportunity-top">
        <div>
          <h3 className="section-subtitle" style={{ margin: 0 }}>
            <span>Opportunity Radar</span>
            <span className="badge badge-medium">{items.length} Tracked</span>
          </h3>
          <p className="muted small" style={{ margin: "4px 0 0" }}>
            Extracted from active emails, Codeforces schedule, and university portals
          </p>
        </div>

        {/* Filter chips */}
        <div className="opp-filters">
          {["all", "internship", "contest", "scholarship"].map((t) => (
            <button
              key={t}
              className={`opp-filter-btn ${filterType === t ? "active" : ""}`}
              onClick={() => setFilterType(t)}
            >
              {t === "all" ? "All Tracks" : `${TYPE_ICONS[t] || ""} ${t}s`}
            </button>
          ))}
        </div>
      </div>

      <div className="opp-grid">
        {filtered.map((item) => (
          <div key={item.key} className="opp-card">
            <div className="opp-card-header">
              <span className="opp-type-badge">
                {TYPE_ICONS[item.type] || "✦"} {item.type}
              </span>
              <span className="opp-source-tag small muted">{item.source}</span>
            </div>

            <h4 className="opp-title">{item.title}</h4>
            <p className="opp-detail small muted">{item.detail}</p>

            <div className="opp-card-footer">
              {item.due ? (
                <span className="opp-due small text-high">Due: {item.due}</span>
              ) : (
                <span className="opp-due small muted">No closing date</span>
              )}

              <div className="opp-actions-row">
                {item.url && (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="opp-link-btn small"
                  >
                    Open ↗
                  </a>
                )}
                <select
                  value={item.status}
                  onChange={(e) => handleStatusChange(item, e.target.value)}
                  className="opp-status-select small"
                >
                  {STATUS_OPTIONS.map((st) => (
                    <option key={st} value={st}>
                      {st.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
