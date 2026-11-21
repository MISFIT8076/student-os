"use client";

import { useCallback, useEffect, useState } from "react";
import BriefingPanel from "@/components/BriefingPanel";
import ChatPanel from "@/components/ChatPanel";
import KairoLogo from "@/components/KairoLogo";
import ThemeToggle from "@/components/ThemeToggle";
import { getBriefing } from "@/lib/api";
import type { Briefing } from "@/lib/types";

export default function Home() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentDateStr, setCurrentDateStr] = useState<string>("");

  useEffect(() => {
    const today = new Date();
    const formatted = today.toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
    });
    setCurrentDateStr(formatted);
  }, []);

  const load = useCallback(async (refresh = false) => {
    setLoading(true);
    setError(null);
    try {
      setBriefing(await getBriefing(refresh));
    } catch (e) {
      setError(
        `Could not reach the Kairo Core API. Ensure uvicorn is active on http://127.0.0.1:8000. (${(e as Error).message})`
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const urgentCount =
    briefing?.items.filter((i) => i.priority === "urgent").length ?? 0;
  const highCount =
    briefing?.items.filter((i) => i.priority === "high").length ?? 0;

  return (
    <main className="wrap">
      {/* Top Navigation Bar */}
      <header className="kairo-topbar">
        <div className="topbar-left">
          <KairoLogo size="md" />
        </div>

        <div className="topbar-right">
          <div className="header-status-pill">
            <span className="live-status-dot pulse" />
            <span className="status-text">{currentDateStr || "Today"}</span>
            <span className="status-divider">·</span>
            <span className="status-platform-text">5 MCP Tools Active</span>
          </div>

          <a className="nav-btn-link" href="/progress" title="View historical habits and streaks">
            <span>Progress & Habits</span>
            <span className="nav-arrow">→</span>
          </a>

          <ThemeToggle />
        </div>
      </header>

      {/* Hero Greek Horizon Bar */}
      <section className="kairo-horizon-bar">
        <div className="horizon-item">
          <div className="horizon-num-wrap text-urgent">
            <span className="horizon-num">{urgentCount}</span>
            {urgentCount > 0 && <span className="horizon-badge-pulse">Crit</span>}
          </div>
          <div className="horizon-label">Critical Focus</div>
        </div>

        <div className="horizon-item">
          <div className="horizon-num-wrap text-high">
            <span className="horizon-num">{highCount}</span>
          </div>
          <div className="horizon-label">High Priority</div>
        </div>

        <div className="horizon-item">
          <div className="horizon-num-wrap text-gold">
            <span className="horizon-num">{briefing?.items.length ?? 0}</span>
          </div>
          <div className="horizon-label">Total Signals Ranked</div>
        </div>

        <div className="horizon-item">
          <div className="horizon-num-wrap text-accent">
            <span className="horizon-num">{briefing?.sources_used.length ?? 5}</span>
          </div>
          <div className="horizon-label">Connected Platforms</div>
        </div>
      </section>

      {/* Main Interactive Grid */}
      <div className="kairo-main-grid">
        <BriefingPanel
          briefing={briefing}
          loading={loading}
          error={error}
          onRefresh={() => load(true)}
        />
        <ChatPanel />
      </div>

      {/* Classical Greek Footer */}
      <footer className="kairo-footer">
        <div className="footer-greek-quote">
          <span className="greek-meander">« καιρῷ πρόσφορα »</span>
          <p className="quote-translation">
            “Act in the opportune moment, for timing is the master of all deeds.”
          </p>
        </div>
        <div className="footer-meta-row">
          <span>Kairo v0.18.0 · BTech Capstone CSE/IT</span>
          <span className="footer-sep">·</span>
          <span>Model Context Protocol (MCP)</span>
          <span className="footer-sep">·</span>
          <a href="/progress">Habit Funnel</a>
          <span className="footer-sep">·</span>
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
          >
            REST API Docs ↗
          </a>
        </div>
      </footer>
    </main>
  );
}
