"use client";

import { useCallback, useEffect, useState } from "react";
import KairoLogo from "@/components/KairoLogo";
import ThemeToggle from "@/components/ThemeToggle";
import { getProgress } from "@/lib/api";
import type { Progress } from "@/lib/types";

function Bars({
  data,
  fillColor = "var(--gold)",
}: {
  data: Record<string, number>;
  fillColor?: string;
}) {
  const entries = Object.entries(data);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  if (entries.length === 0)
    return <p className="muted small">No historical data recorded yet.</p>;

  return (
    <div className="bars-list">
      {entries.map(([label, value]) => (
        <div key={label} className="bar-row">
          <span className="bar-label">{label.replace(/_/g, " ")}</span>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{
                width: `${(value / max) * 100}%`,
                background: fillColor,
              }}
            />
          </div>
          <span className="bar-val font-mono">{value}</span>
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
      {/* Top Bar */}
      <header className="kairo-topbar">
        <div className="topbar-left">
          <KairoLogo size="md" />
        </div>

        <div className="topbar-right">
          <a className="nav-btn-link" href="/">
            <span className="nav-arrow">←</span>
            <span>Return to Today</span>
          </a>
          <ThemeToggle />
        </div>
      </header>

      {/* Progress Header Hero */}
      <div className="progress-hero-card">
        <h1 className="progress-title">Academic Momentum & Habits</h1>
        <p className="muted">
          Tracking the rhythm of execution across your semester. Kairos honors consistency.
        </p>
      </div>

      {error && (
        <div className="alert" style={{ marginBottom: "20px" }}>
          Could not load progress records: {error}
        </div>
      )}

      {data && (
        <div className="progress-grid">
          {/* Key Metric Pillars */}
          <section className="panel progress-stat-panel">
            <h2 className="panel-title">
              <span>Pillars of Momentum</span>
            </h2>
            <div className="pillar-stats-grid">
              <div className="pillar-card">
                <span className="pillar-icon">🔥</span>
                <div className="pillar-number font-mono text-gold">
                  {data.done_streak_days}
                </div>
                <div className="pillar-label">Day Done-Streak</div>
                <div className="pillar-sub small muted">Consecutive active days</div>
              </div>

              <div className="pillar-card">
                <span className="pillar-icon">⚡</span>
                <div className="pillar-number font-mono text-accent">
                  {data.total_actions}
                </div>
                <div className="pillar-label">Decisive Actions</div>
                <div className="pillar-sub small muted">Tasks resolved</div>
              </div>

              <div className="pillar-card">
                <span className="pillar-icon">👁️</span>
                <div className="pillar-number font-mono text-high">
                  {data.items_shown}
                </div>
                <div className="pillar-label">Signals Surfaced</div>
                <div className="pillar-sub small muted">Cross-platform items</div>
              </div>
            </div>
          </section>

          {/* Action Types Distribution */}
          <section className="panel">
            <h2 className="panel-title">Action Types Executed</h2>
            <p className="muted small" style={{ marginBottom: "16px" }}>
              Distribution of resolved tasks, commits, PR approvals, and submissions
            </p>
            <Bars data={data.actions} fillColor="var(--accent)" />
          </section>

          {/* Opportunity & Application Funnel */}
          <section className="panel">
            <h2 className="panel-title">Opportunity Pipeline Funnel</h2>
            <p className="muted small" style={{ marginBottom: "16px" }}>
              Active tracking for internships, scholarships, and competitive contests
            </p>
            <Bars data={data.application_funnel} fillColor="var(--gold)" />
          </section>
        </div>
      )}

      <footer className="kairo-footer" style={{ marginTop: "40px" }}>
        <div className="footer-meta-row">
          <a href="/">← Return to Today&apos;s Focus</a>
          <span className="footer-sep">·</span>
          <span>Kairo Habit Engine</span>
        </div>
      </footer>
    </main>
  );
}
