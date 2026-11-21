"use client";

import { useMemo, useState } from "react";
import type { Briefing } from "@/lib/types";
import PriorityBadge from "./PriorityBadge";
import ScheduleView from "./ScheduleView";
import OpportunityView from "./OpportunityView";

const SOURCE_META: Record<
  string,
  { label: string; icon: string; color: string; badge: string }
> = {
  github: { label: "GitHub", icon: "⑂", color: "#8b5cf6", badge: "src-gh" },
  gmail: { label: "Gmail", icon: "✉", color: "#ef4444", badge: "src-mail" },
  calendar: { label: "Calendar", icon: "◷", color: "#0284c7", badge: "src-cal" },
  codeforces: { label: "Codeforces", icon: "⚔", color: "#f59e0b", badge: "src-cf" },
  classroom: { label: "Classroom", icon: "🎓", color: "#10b981", badge: "src-class" },
};

function daysLabel(due?: string | null): { text: string; urgent: boolean } | null {
  if (!due) return null;
  const d = new Date(due);
  const today = new Date();
  d.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  const diff = Math.round((d.getTime() - today.getTime()) / 86400000);
  if (diff < 0) return { text: `${-diff}d overdue`, urgent: true };
  if (diff === 0) return { text: "due today", urgent: true };
  if (diff === 1) return { text: "due tomorrow", urgent: false };
  return { text: `due in ${diff}d`, urgent: false };
}

export default function BriefingPanel({
  briefing,
  loading,
  error,
  onRefresh,
}: {
  briefing: Briefing | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  const [activeTab, setActiveTab] = useState<"priorities" | "schedule" | "radar">(
    "priorities"
  );
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState<string>("all");

  const filteredItems = useMemo(() => {
    if (!briefing) return [];
    return briefing.items.filter((it) => {
      const matchSource =
        sourceFilter === "all" || it.source.toLowerCase() === sourceFilter.toLowerCase();
      const matchSearch =
        !search ||
        it.title.toLowerCase().includes(search.toLowerCase()) ||
        it.detail.toLowerCase().includes(search.toLowerCase());
      return matchSource && matchSearch;
    });
  }, [briefing, sourceFilter, search]);

  return (
    <section className="panel main-briefing-panel">
      {/* Panel Top Nav */}
      <div className="briefing-panel-nav">
        <div className="view-mode-tabs">
          <button
            className={`view-tab-btn ${activeTab === "priorities" ? "active" : ""}`}
            onClick={() => setActiveTab("priorities")}
          >
            <span className="tab-icon">✦</span>
            <span>Priorities</span>
            {briefing && (
              <span className="tab-count-pill">{briefing.items.length}</span>
            )}
          </button>
          <button
            className={`view-tab-btn ${activeTab === "schedule" ? "active" : ""}`}
            onClick={() => setActiveTab("schedule")}
          >
            <span className="tab-icon">◷</span>
            <span>Day Schedule</span>
          </button>
          <button
            className={`view-tab-btn ${activeTab === "radar" ? "active" : ""}`}
            onClick={() => setActiveTab("radar")}
          >
            <span className="tab-icon">◎</span>
            <span>Opportunities</span>
          </button>
        </div>

        <button
          className="btn btn-secondary btn-refresh"
          onClick={onRefresh}
          disabled={loading}
          title="Re-synchronize all connected MCP platforms"
        >
          <span className={`refresh-icon ${loading ? "spinning" : ""}`}>↻</span>
          <span>{loading ? "Aligning…" : "Sync"}</span>
        </button>
      </div>

      {error && <div className="alert">{error}</div>}

      {/* VIEW 1: RANKED PRIORITIES */}
      {activeTab === "priorities" && (
        <>
          {briefing && (
            <>
              {/* Classical Kairos Banner */}
              <div className="kairos-headline-banner">
                <div className="headline-meta-row">
                  <span className="meta-badge-intelligence">
                    <span className="pulse-dot" />
                    {briefing.llm_used ? "Claude LLM Synthesizer" : "Rule-Based Prioritizer"}
                  </span>
                  <span className="meta-badge-status">
                    {briefing.cached ? "Cached Snapshot" : "Live MCP Sync"}
                  </span>
                  <span className="meta-badge-sources">
                    {briefing.sources_used.length} Platforms Online
                  </span>
                </div>

                <h3 className="kairos-headline-text">{briefing.headline}</h3>
                <p className="kairos-summary-text">{briefing.summary}</p>

                {/* Sources list */}
                {briefing.sources_used.length > 0 && (
                  <div className="sources-pills-row">
                    <span className="sources-label small muted">Active Integrations:</span>
                    {briefing.sources_used.map((src) => {
                      const meta = SOURCE_META[src] || {
                        label: src,
                        icon: "●",
                        color: "var(--accent)",
                      };
                      return (
                        <span
                          key={src}
                          className="source-indicator-pill"
                          style={{ borderColor: `${meta.color}44` }}
                        >
                          <span
                            className="source-color-dot"
                            style={{ background: meta.color }}
                          />
                          <span className="source-pill-name">{meta.label}</span>
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Filter and Search Bar */}
              <div className="items-filter-bar">
                <div className="search-wrap">
                  <span className="search-icon">🔍</span>
                  <input
                    type="text"
                    placeholder="Search prioritized tasks, courses, PRs…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="kairo-search-input"
                  />
                  {search && (
                    <button
                      className="search-clear-btn"
                      onClick={() => setSearch("")}
                    >
                      ×
                    </button>
                  )}
                </div>

                <div className="source-filter-chips">
                  <button
                    className={`filter-chip ${sourceFilter === "all" ? "active" : ""}`}
                    onClick={() => setSourceFilter("all")}
                  >
                    All ({briefing.items.length})
                  </button>
                  {briefing.sources_used.map((src) => {
                    const count = briefing.items.filter((i) => i.source === src).length;
                    const meta = SOURCE_META[src] || { label: src };
                    return (
                      <button
                        key={src}
                        className={`filter-chip ${sourceFilter === src ? "active" : ""}`}
                        onClick={() => setSourceFilter(src)}
                      >
                        {meta.label} ({count})
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Items List */}
              <ul className="items-list">
                {filteredItems.map((it, i) => {
                  const meta = SOURCE_META[it.source] || {
                    label: it.source,
                    icon: "●",
                    color: "var(--accent)",
                  };
                  const dueInfo = daysLabel(it.due);

                  return (
                    <li
                      key={`${it.source}-${i}`}
                      className={`kairo-item-card priority-${it.priority}`}
                    >
                      <div
                        className="item-source-badge"
                        style={{
                          backgroundColor: `${meta.color}18`,
                          borderColor: `${meta.color}40`,
                          color: meta.color,
                        }}
                        title={`Platform: ${meta.label}`}
                      >
                        <span className="src-icon">{meta.icon}</span>
                        <span className="src-label">{meta.label}</span>
                      </div>

                      <div className="item-main-content">
                        <div className="item-title-row">
                          <PriorityBadge priority={it.priority} />
                          {it.url ? (
                            <a
                              href={it.url}
                              target="_blank"
                              rel="noreferrer"
                              className="item-title-link"
                            >
                              {it.title}
                              <span className="external-link-arrow">↗</span>
                            </a>
                          ) : (
                            <span className="item-title-text">{it.title}</span>
                          )}
                        </div>

                        <div className="item-detail-row">
                          <span className="item-kind-tag">#{it.kind}</span>
                          <span className="item-detail-text">{it.detail}</span>

                          {dueInfo && (
                            <span
                              className={`due-pill ${dueInfo.urgent ? "due-urgent" : "due-normal"}`}
                            >
                              ◷ {dueInfo.text}
                            </span>
                          )}
                        </div>
                      </div>
                    </li>
                  );
                })}

                {filteredItems.length === 0 && (
                  <div className="no-items-state">
                    <p className="muted">No items matched your current filter criteria.</p>
                    <button
                      className="btn btn-secondary small"
                      onClick={() => {
                        setSearch("");
                        setSourceFilter("all");
                      }}
                    >
                      Reset filters
                    </button>
                  </div>
                )}
              </ul>
            </>
          )}

          {!briefing && !error && !loading && (
            <div className="no-items-state">
              <p className="muted">No briefing available. Click Sync to gather data.</p>
            </div>
          )}
        </>
      )}

      {/* VIEW 2: KAIROS DAY SCHEDULE */}
      {activeTab === "schedule" && <ScheduleView />}

      {/* VIEW 3: OPPORTUNITY RADAR */}
      {activeTab === "radar" && <OpportunityView />}
    </section>
  );
}
