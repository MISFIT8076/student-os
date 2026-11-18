"use client";

import { useCallback, useEffect, useState } from "react";
import { getProgress } from "@/lib/api";
import type { Progress } from "@/lib/types";

function Bars({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  if (entries.length === 0) return <p className="muted small">No data yet.</p>;
  return (
    <div className="bars">
      {entries.map(([label, value]) => (
        <div key={label} className="bar-row">
          <span className="bar-label">{label}</span>
          <span className="bar-track">
            <span className="bar-fill" style={{ width: `${(value / max) * 100}%` }} />
          </span>
          <span className="bar-val">{value}</span>
        </div>
      ))}
    </div>
  );
}

export default function ProgressPage() {
  const [data, setData] = useState<Progress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setData(await getProgress());
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <main className="wrap">
      <header className="topbar">
        <div className="brand">
          <span className="logo">◎</span>
          <div>
            <h1>Your progress</h1>
            <p className="muted small">Habits and follow-through over time</p>
          </div>
        </div>
      </header>

      {error && <div className="alert">Could not load progress: {error}</div>}

      {data && (
        <div className="grid">
          <section className="panel">
            <div className="panel-head"><h2>At a glance</h2></div>
            <div className="stat-row">
              <div className="stat">
                <div className="stat-num">{data.done_streak_days}</div>
                <div className="muted small">day done-streak</div>
              </div>
              <div className="stat">
                <div className="stat-num">{data.total_actions}</div>
                <div className="muted small">actions taken</div>
              </div>
              <div className="stat">
                <div className="stat-num">{data.items_shown}</div>
                <div className="muted small">items surfaced</div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-head"><h2>Actions</h2></div>
            <Bars data={data.actions} />
          </section>

          <section className="panel">
            <div className="panel-head"><h2>Application funnel</h2></div>
            <Bars data={data.application_funnel} />
          </section>
        </div>
      )}

      <footer className="foot muted small">
        <a href="/">← back to today</a>
      </footer>
    </main>
  );
}
