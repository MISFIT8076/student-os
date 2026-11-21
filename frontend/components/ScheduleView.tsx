"use client";

import { useEffect, useState } from "react";
import { getSchedule } from "@/lib/api";
import type { DaySchedule } from "@/lib/types";

const SOURCE_COLORS: Record<string, string> = {
  github: "#8b5cf6",
  gmail: "#ef4444",
  calendar: "#0284c7",
  codeforces: "#f59e0b",
  classroom: "#10b981",
};

export default function ScheduleView() {
  const [schedule, setSchedule] = useState<DaySchedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSchedule()
      .then((data) => setSchedule(data))
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="schedule-loading">
        <div className="kairo-spinner" />
        <p className="muted small">Calculating Kairos time-blocks & wellbeing balance…</p>
      </div>
    );
  }

  if (error || !schedule) {
    return (
      <div className="alert">
        Could not load schedule: {error || "Unavailable"}
      </div>
    );
  }

  const {
    blocks,
    overflow,
    available_minutes,
    demand_minutes,
    scheduled_minutes,
    overcommitted,
    advice,
  } = schedule;

  const usagePercent = Math.min(
    100,
    Math.round((scheduled_minutes / Math.max(1, available_minutes)) * 100)
  );

  return (
    <div className="schedule-container">
      {/* Wellbeing & Advice Banner */}
      <div className={`schedule-advice-card ${overcommitted ? "is-overcommitted" : "is-balanced"}`}>
        <div className="advice-header">
          <span className="advice-icon">{overcommitted ? "⚖️" : "✨"}</span>
          <div>
            <h4 className="advice-title">
              {overcommitted ? "Wellbeing Alert: Day Overcommitted" : "Harmonious Day Balance"}
            </h4>
            <p className="advice-text">{advice}</p>
          </div>
        </div>

        {/* Hour Capacity Progress */}
        <div className="capacity-bar-wrap">
          <div className="capacity-labels small">
            <span>
              Scheduled: <strong>{Math.floor(scheduled_minutes / 60)}h {scheduled_minutes % 60}m</strong>
            </span>
            <span>
              Available: <strong>{Math.floor(available_minutes / 60)}h {available_minutes % 60}m</strong>
            </span>
            <span>
              Demand: <strong className={overcommitted ? "text-urgent" : ""}>{Math.floor(demand_minutes / 60)}h {demand_minutes % 60}m</strong>
            </span>
          </div>
          <div className="capacity-track">
            <div
              className={`capacity-fill ${overcommitted ? "fill-warning" : "fill-optimal"}`}
              style={{ width: `${usagePercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Time-blocked Agenda */}
      <div className="timeline-section">
        <h3 className="section-subtitle">
          <span>Today&apos;s Chronological Horizon</span>
          <span className="badge badge-low">{blocks.length} Blocks Placed</span>
        </h3>

        <div className="timeline-flow">
          {blocks.map((b, idx) => (
            <div key={`${b.start}-${idx}`} className="timeline-block-card">
              <div className="timeline-time-col">
                <span className="time-start">{b.start}</span>
                <span className="time-line" />
                <span className="time-end">{b.end}</span>
              </div>

              <div className="timeline-content-card">
                <div className="timeline-item-header">
                  <span
                    className="timeline-source-dot"
                    style={{ background: SOURCE_COLORS[b.source] || "var(--accent)" }}
                    title={b.source}
                  />
                  <span className="timeline-source-tag">{b.source}</span>
                  <span className="timeline-kind-tag">· {b.kind}</span>
                  <span className="timeline-duration-badge">{b.minutes} min</span>
                </div>
                <div className="timeline-item-title">{b.title}</div>
                {b.due && <div className="timeline-item-due small muted">Deadline: {b.due}</div>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Deferred Overflow Section */}
      {overflow.length > 0 && (
        <div className="overflow-section">
          <h3 className="section-subtitle">
            <span className="text-urgent">Deferred for Wellbeing</span>
            <span className="badge badge-urgent">{overflow.length} Deferred</span>
          </h3>
          <p className="muted small" style={{ marginBottom: "10px" }}>
            These lower-priority tasks were strategically placed in reserve to prevent burnout today.
          </p>
          <div className="overflow-grid">
            {overflow.map((ov, i) => (
              <div key={i} className="overflow-card">
                <div className="overflow-header small muted">
                  <span className="capitalize">{ov.source}</span> · {ov.kind} ({ov.minutes}m)
                </div>
                <div className="overflow-title">{ov.title}</div>
                {ov.due && <div className="overflow-due small">Due: {ov.due}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
