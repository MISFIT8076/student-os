"use client";

import { useEffect, useState, useMemo } from "react";
import type { ActionItem } from "@/lib/types";
import PriorityBadge from "./PriorityBadge";
import ThemeToggle from "./ThemeToggle";

interface FocusModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  items: ActionItem[];
  onMarkDone?: (item: ActionItem) => void;
}

const SPOTIFY_PLAYLISTS = [
  { id: "37i9dQZF1DWWQRwui0ExPn", name: "☕ Lofi Beats", desc: "Chill beats for focus" },
  { id: "37i9dQZF1DWZeKCadgRdKQ", name: "🧠 Deep Focus", desc: "Ambient & alpha waves" },
  { id: "37i9dQZF1DWVfe3KKLfQdk", name: "🎻 Classical Study", desc: "Calm classical mastery" },
  { id: "37i9dQZF1DXdLEN7aqioXM", name: "⚡ Synthwave Coding", desc: "Retro electro flow" },
  { id: "37i9dQZF1DX4sWSpwq3LiO", name: "🎹 Peaceful Piano", desc: "Gentle piano focus" },
];

function getInitialDuration(kind?: string): number {
  switch (kind) {
    case "exam":
      return 60 * 60; // 60 mins
    case "deadline":
      return 45 * 60; // 45 mins
    case "pull_request":
    case "issue":
      return 30 * 60; // 30 mins
    case "contest":
    case "practice":
      return 45 * 60; // 45 mins
    default:
      return 25 * 60; // 25 mins Pomodoro
  }
}

export default function FocusModeModal({ isOpen, onClose, items, onMarkDone }: FocusModeModalProps) {
  const [taskIndex, setTaskIndex] = useState(0);
  const currentTask = items[taskIndex] || null;

  // Timer states
  const initialDuration = useMemo(
    () => getInitialDuration(currentTask?.kind),
    [currentTask?.kind]
  );
  const [totalTime, setTotalTime] = useState(initialDuration);
  const [timeLeft, setTimeLeft] = useState(initialDuration);
  const [isRunning, setIsRunning] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);

  // Spotify states
  const [showSpotify, setShowSpotify] = useState(true);
  const [isExpandedPlayer, setIsExpandedPlayer] = useState(false);
  const [selectedPlaylist, setSelectedPlaylist] = useState(SPOTIFY_PLAYLISTS[0].id);
  const [customLink, setCustomLink] = useState("");
  const [customEmbedUrl, setCustomEmbedUrl] = useState<string | null>(null);
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Sync initial timer when task changes
  useEffect(() => {
    const dur = getInitialDuration(currentTask?.kind);
    setTotalTime(dur);
    setTimeLeft(dur);
    setIsRunning(false);
    setIsCompleted(false);
  }, [currentTask]);

  // Timer countdown
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isRunning && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (timeLeft === 0 && isRunning) {
      setIsRunning(false);
      setIsCompleted(true);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning, timeLeft]);

  // Handle escape key to exit
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Formatting minutes and seconds
  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  const timeFormatted = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  // SVG Progress calculation
  const progressPercent = totalTime > 0 ? (timeLeft / totalTime) * 100 : 0;
  const radius = 100;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progressPercent / 100) * circumference;

  const handlePreset = (mins: number) => {
    const secs = mins * 60;
    setTotalTime(secs);
    setTimeLeft(secs);
    setIsRunning(false);
    setIsCompleted(false);
  };

  const handleApplyCustomSpotify = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = customLink.trim();
    if (!trimmed) return;

    // Support links like:
    // https://open.spotify.com/playlist/...
    // https://open.spotify.com/album/...
    // https://open.spotify.com/track/...
    const match = trimmed.match(/open\.spotify\.com\/(playlist|album|track|artist)\/([a-zA-Z0-9]+)/);
    if (match) {
      const type = match[1];
      const id = match[2];
      setCustomEmbedUrl(`https://open.spotify.com/embed/${type}/${id}?utm_source=generator&theme=0`);
      setShowCustomInput(false);
    } else {
      alert("Please paste a valid Spotify playlist, album, or track URL.");
    }
  };

  const activeEmbedSrc =
    customEmbedUrl ||
    `https://open.spotify.com/embed/playlist/${selectedPlaylist}?utm_source=generator&theme=0`;

  return (
    <div className="focus-fullscreen-sanctuary">
      {/* Dynamic Animated Ambient Orbs */}
      <div className="focus-mesh-orb orb-gold" />
      <div className="focus-mesh-orb orb-blue" />
      <div className="focus-mesh-orb orb-violet" />

      {/* iPhone Glass Mirror Surface Reflection Layer */}
      <div className="focus-mirror-sheen" />

      {/* Main Fullscreen Chamber Wrapper */}
      <div className="focus-chamber-full">
        {/* Top Floating Glass Header */}
        <header className="focus-chamber-header">
          <div className="focus-brand-pill">
            <span className="focus-sparkle">✦</span>
            <span className="focus-brand-text">KAIROS FOCUS SANCTUARY</span>
          </div>

          <div className="focus-center-status">
            <span className="focus-live-dot pulse" />
            <span className="focus-status-motto">One Task · Zero Noise · Supreme Flow</span>
          </div>

          <div className="focus-header-actions">
            <ThemeToggle />
            <button
              className="focus-exit-btn"
              onClick={onClose}
              title="Exit Super Focus Sanctuary (Esc)"
            >
              <span>Exit Focus</span>
              <span className="esc-key">Esc</span>
            </button>
          </div>
        </header>

        {/* Central Monastic Core */}
        <main className="focus-central-core">
          {currentTask ? (
            <div className="focus-core-layout">
              {/* Task Glass Island */}
              <section className="focus-task-island">
                <div className="focus-task-meta">
                  <span className="focus-source-tag capitalize">
                    {currentTask.source} · #{currentTask.kind}
                  </span>
                  <PriorityBadge priority={currentTask.priority} />
                  {items.length > 1 && (
                    <div className="focus-task-stepper">
                      <button
                        className="stepper-btn"
                        disabled={taskIndex === 0}
                        onClick={() => setTaskIndex((i) => Math.max(0, i - 1))}
                        title="Previous task"
                      >
                        ←
                      </button>
                      <span className="stepper-count">
                        {taskIndex + 1} of {items.length}
                      </span>
                      <button
                        className="stepper-btn"
                        disabled={taskIndex >= items.length - 1}
                        onClick={() => setTaskIndex((i) => Math.min(items.length - 1, i + 1))}
                        title="Next task"
                      >
                        →
                      </button>
                    </div>
                  )}
                </div>

                <h1 className="focus-task-title">{currentTask.title}</h1>

                {currentTask.detail && (
                  <p className="focus-task-detail">{currentTask.detail}</p>
                )}

                {currentTask.due && (
                  <div className="focus-task-due">
                    <span className="due-icon">⏰</span>
                    <span>Deadline: {currentTask.due}</span>
                  </div>
                )}
              </section>

              {/* iPhone Glass Circular Countdown Timer */}
              <section className="focus-timer-island">
                <div className="timer-ring-container">
                  <svg className="timer-svg" width="260" height="260" viewBox="0 0 260 260">
                    <defs>
                      <linearGradient id="timerMirrorGold" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#fef08a" />
                        <stop offset="50%" stopColor="#f59e0b" />
                        <stop offset="100%" stopColor="#d97706" />
                      </linearGradient>
                    </defs>
                    {/* Background Track */}
                    <circle
                      className="timer-track"
                      cx="130"
                      cy="130"
                      r={radius}
                      strokeWidth="7"
                    />
                    {/* Progress Circle */}
                    <circle
                      className="timer-progress"
                      cx="130"
                      cy="130"
                      r={radius}
                      strokeWidth="8"
                      strokeDasharray={circumference}
                      strokeDashoffset={strokeDashoffset}
                    />
                  </svg>

                  {/* Inside Clock */}
                  <div className="timer-center-info">
                    <span className={`timer-digits font-mono ${isRunning ? "active-glow" : ""}`}>
                      {timeFormatted}
                    </span>
                    <span className="timer-phase-label">
                      {isCompleted
                        ? "Completed! 🎉"
                        : isRunning
                        ? "Deep Focus Active"
                        : "Paused"}
                    </span>
                  </div>
                </div>

                {/* Primary Action Controls */}
                <div className="timer-controls-row">
                  <button
                    className={`focus-btn-primary ${isRunning ? "is-running" : ""}`}
                    onClick={() => setIsRunning(!isRunning)}
                  >
                    <span className="btn-icon">{isRunning ? "❚❚" : "▶"}</span>
                    <span>{isRunning ? "Pause Flow" : "Commence Focus"}</span>
                  </button>

                  <button
                    className="focus-btn-secondary"
                    onClick={() => {
                      setIsRunning(false);
                      setTimeLeft(totalTime);
                      setIsCompleted(false);
                    }}
                    title="Reset Timer"
                  >
                    <span>↺ Reset</span>
                  </button>

                  <button
                    className="focus-btn-complete"
                    onClick={() => {
                      setIsRunning(false);
                      setIsCompleted(true);
                      if (currentTask) {
                        onMarkDone?.(currentTask);
                      }
                    }}
                    title="Mark this task as finished"
                  >
                    <span>✓ Done</span>
                  </button>
                </div>

                {/* Presets Row */}
                <div className="timer-presets-row">
                  <span className="presets-label small muted">Pacing:</span>
                  <button
                    className={`preset-chip ${totalTime === 25 * 60 ? "active" : ""}`}
                    onClick={() => handlePreset(25)}
                  >
                    25m Pomodoro
                  </button>
                  <button
                    className={`preset-chip ${totalTime === 45 * 60 ? "active" : ""}`}
                    onClick={() => handlePreset(45)}
                  >
                    45m Deep Work
                  </button>
                  <button
                    className={`preset-chip ${totalTime === 90 * 60 ? "active" : ""}`}
                    onClick={() => handlePreset(90)}
                  >
                    90m Flow State
                  </button>
                </div>
              </section>
            </div>
          ) : (
            <div className="focus-empty-card">
              <h2>You are in clear horizon!</h2>
              <p className="muted">No prioritized tasks remaining for today. Enjoy the breathing room.</p>
              <button className="btn btn-secondary" onClick={onClose}>
                Return to Dashboard
              </button>
            </div>
          )}
        </main>

        {/* Floating Glass Spotify Audio Dock */}
        <footer className="focus-dock-island">
          <div className="spotify-dock-bar">
            <div className="spotify-dock-header">
              <div className="spotify-title-group">
                <span className="spotify-icon-brand">🎧</span>
                <span className="spotify-bar-heading">Focus Audio (Spotify)</span>
                <span className="spotify-status-badge">Ambient & Flow</span>
              </div>

              <div className="spotify-quick-buttons">
                {SPOTIFY_PLAYLISTS.map((pl) => (
                  <button
                    key={pl.id}
                    className={`spotify-preset-btn ${
                      !customEmbedUrl && selectedPlaylist === pl.id ? "active" : ""
                    }`}
                    onClick={() => {
                      setCustomEmbedUrl(null);
                      setSelectedPlaylist(pl.id);
                    }}
                    title={pl.desc}
                  >
                    {pl.name}
                  </button>
                ))}

                <button
                  className={`spotify-custom-toggle-btn ${showCustomInput ? "active" : ""}`}
                  onClick={() => setShowCustomInput(!showCustomInput)}
                >
                  + Custom Link
                </button>

                <button
                  className="spotify-collapse-btn"
                  onClick={() => setIsExpandedPlayer(!isExpandedPlayer)}
                  title="Toggle player size"
                >
                  {isExpandedPlayer ? "Compact" : "Expand"}
                </button>

                <button
                  className="spotify-collapse-btn"
                  onClick={() => setShowSpotify(!showSpotify)}
                >
                  {showSpotify ? "Hide Player" : "Show Player"}
                </button>
              </div>
            </div>

            {/* Custom Spotify URL Input Dialog */}
            {showCustomInput && (
              <form className="spotify-custom-form" onSubmit={handleApplyCustomSpotify}>
                <input
                  type="text"
                  placeholder="Paste your Spotify playlist or album URL (e.g. https://open.spotify.com/playlist/...)"
                  value={customLink}
                  onChange={(e) => setCustomLink(e.target.value)}
                  className="spotify-url-input"
                  autoFocus
                />
                <button type="submit" className="btn btn-primary small">
                  Load Music
                </button>
              </form>
            )}

            {/* Embedded Spotify IFrame */}
            {showSpotify && (
              <div className="spotify-embed-container">
                <iframe
                  title="Kairo Spotify Focus Stream"
                  src={activeEmbedSrc}
                  width="100%"
                  height={isExpandedPlayer ? "152" : "80"}
                  frameBorder="0"
                  allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                  loading="lazy"
                  style={{ borderRadius: "14px", border: "none" }}
                />
              </div>
            )}
          </div>
        </footer>
      </div>
    </div>
  );
}
