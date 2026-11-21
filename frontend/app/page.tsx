"use client";

import { useCallback, useEffect, useState } from "react";
import BriefingPanel from "@/components/BriefingPanel";
import ChatPanel from "@/components/ChatPanel";
import KairoLogo from "@/components/KairoLogo";
import ThemeToggle from "@/components/ThemeToggle";
import AuthModal from "@/components/AuthModal";
import IntegrationsModal from "@/components/IntegrationsModal";
import FocusModeModal from "@/components/FocusModeModal";
import { getBriefing, getStoredUser, clearAuth, getConnections } from "@/lib/api";
import type { Briefing, User } from "@/lib/types";

export default function Home() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentDateStr, setCurrentDateStr] = useState<string>("");
  const [isFocusOpen, setIsFocusOpen] = useState(false);

  // Keyboard shortcut: Press 'F' to toggle focus mode
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeEl = document.activeElement;
      const isInput =
        activeEl?.tagName === "INPUT" ||
        activeEl?.tagName === "TEXTAREA" ||
        (activeEl as HTMLElement)?.isContentEditable;
      if (e.key.toLowerCase() === "f" && !isInput && !e.metaKey && !e.ctrlKey) {
        setIsFocusOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Auth & Integrations state
  const [user, setUser] = useState<User | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [integrationsModalOpen, setIntegrationsModalOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [connectedAppsCount, setConnectedAppsCount] = useState<number>(0);

  const refreshConnectionsCount = useCallback(async () => {
    try {
      const conns = await getConnections();
      setConnectedAppsCount(conns.filter((c) => c.is_connected).length);
    } catch {
      // Mock/unauthed fallback
    }
  }, []);

  useEffect(() => {
    const today = new Date();
    const formatted = today.toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
    });
    setCurrentDateStr(formatted);
    setUser(getStoredUser());
    refreshConnectionsCount();
  }, [refreshConnectionsCount]);

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

  function handleSignOut() {
    clearAuth();
    setUser(null);
    setUserMenuOpen(false);
    refreshConnectionsCount();
    load(true);
  }

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

          {/* Connected Apps Hub Button */}
          <button
            type="button"
            className="apps-hub-trigger"
            onClick={() => setIntegrationsModalOpen(true)}
            title="Configure API keys, handles, and tool connections"
          >
            <span>🔌 Connected Apps</span>
            {connectedAppsCount > 0 ? (
              <span className="status-tag connected">{connectedAppsCount}/5</span>
            ) : (
              <span className="status-tag pending">Setup</span>
            )}
          </button>

          {/* Super Focus Mode Chamber Trigger */}
          <button
            className="super-focus-btn"
            onClick={() => setIsFocusOpen(true)}
            title="Enter Super Focus Sanctuary (Press F)"
          >
            <span className="focus-btn-sparkle">✦</span>
            <span className="focus-btn-label">Super Focus</span>
            <span className="focus-btn-shortcut">F</span>
          </button>

          <a className="nav-btn-link" href="/progress" title="View historical habits and streaks">
            <span>Progress & Habits</span>
            <span className="nav-arrow">→</span>
          </a>

          {/* User Profile / Sign In */}
          {user ? (
            <div className="user-profile-menu-wrap">
              <button
                type="button"
                className="user-profile-trigger"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
              >
                <div className="user-avatar-circle">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <span>{user.name.split(" ")[0]}</span>
                <span style={{ fontSize: "10px" }}>▾</span>
              </button>

              {userMenuOpen && (
                <div className="user-dropdown-card">
                  <div style={{ padding: "6px 12px", borderBottom: "1px solid var(--border-subtle)" }}>
                    <div style={{ fontSize: "12px", fontWeight: 600 }}>{user.name}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{user.email}</div>
                  </div>
                  <button
                    type="button"
                    className="user-dropdown-item"
                    onClick={() => {
                      setUserMenuOpen(false);
                      setIntegrationsModalOpen(true);
                    }}
                  >
                    <span>⚙️ App Connections</span>
                  </button>
                  <button
                    type="button"
                    className="user-dropdown-item signout"
                    onClick={handleSignOut}
                  >
                    <span>🚪 Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              type="button"
              className="btn-signin-nav"
              onClick={() => setAuthModalOpen(true)}
            >
              <span>✦ Sign In</span>
            </button>
          )}

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

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={(loggedUser) => {
          setUser(loggedUser);
          refreshConnectionsCount();
          load(true);
        }}
      />

      {/* Connected Apps & Integrations Modal */}
      <IntegrationsModal
        isOpen={integrationsModalOpen}
        onClose={() => setIntegrationsModalOpen(false)}
        onConnectionsUpdated={() => {
          refreshConnectionsCount();
          load(true);
        }}
      />

      {/* Super Focus Mode Chamber */}
      <FocusModeModal
        isOpen={isFocusOpen}
        onClose={() => setIsFocusOpen(false)}
        items={briefing?.items ?? []}
      />
    </main>
  );
}
