import type { Briefing } from "@/lib/types";
import PriorityBadge from "./PriorityBadge";

const SOURCE_ICON: Record<string, string> = {
  github: "GH",
  gmail: "@",
  calendar: "Cal",
  codeforces: "CF",
  classroom: "CR",
};

function daysLabel(due?: string | null): string | null {
  if (!due) return null;
  const d = new Date(due);
  const today = new Date();
  d.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  const diff = Math.round((d.getTime() - today.getTime()) / 86400000);
  if (diff < 0) return `${-diff}d overdue`;
  if (diff === 0) return "due today";
  if (diff === 1) return "due tomorrow";
  return `due in ${diff}d`;
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
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Today&apos;s briefing</h2>
          {briefing && (
            <p className="muted small">
              {briefing.sources_used.length} sources ·{" "}
              {briefing.llm_used ? "LLM planner" : "rule-based planner"} ·{" "}
              {briefing.cached ? "cached" : "fresh"}
            </p>
          )}
        </div>
        <button className="btn" onClick={onRefresh} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {error && <div className="alert">{error}</div>}

      {briefing && (
        <>
          <div className="headline">
            <h3>{briefing.headline}</h3>
            <p className="muted">{briefing.summary}</p>
          </div>

          <ul className="items">
            {briefing.items.map((it, i) => (
              <li key={`${it.source}-${i}`} className="item">
                <span className="src" title={it.source}>
                  {SOURCE_ICON[it.source] ?? it.source}
                </span>
                <div className="item-body">
                  <div className="item-top">
                    <PriorityBadge priority={it.priority} />
                    {it.url ? (
                      <a href={it.url} target="_blank" rel="noreferrer">
                        {it.title}
                      </a>
                    ) : (
                      <span>{it.title}</span>
                    )}
                  </div>
                  <div className="item-meta muted small">
                    {it.detail}
                    {daysLabel(it.due) && (
                      <span className="due"> · {daysLabel(it.due)}</span>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

      {!briefing && !error && !loading && (
        <p className="muted">No briefing yet.</p>
      )}
    </section>
  );
}
