"use client";

import { useCallback, useEffect, useState } from "react";
import BriefingPanel from "@/components/BriefingPanel";
import ChatPanel from "@/components/ChatPanel";
import { getBriefing } from "@/lib/api";
import type { Briefing } from "@/lib/types";

export default function Home() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (refresh = false) => {
    setLoading(true);
    setError(null);
    try {
      setBriefing(await getBriefing(refresh));
    } catch (e) {
      setError(
        `Could not reach the backend. Is it running on the API base URL? (${(e as Error).message})`,
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <main className="wrap">
      <header className="topbar" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div className="brand">
          <span className="logo">◎</span>
          <div>
            <h1>Student OS</h1>
            <p className="muted small">
              One question instead of eight apps — “What should I do today?”
            </p>
          </div>
        </div>
        <a className="nav-link" href="/progress">Progress →</a>
      </header>

      <div className="grid">
        <BriefingPanel
          briefing={briefing}
          loading={loading}
          error={error}
          onRefresh={() => load(true)}
        />
        <ChatPanel />
      </div>

      <footer className="foot muted small">
        BTech Final Year Project · MCP-powered coordination layer
      </footer>
    </main>
  );
}
