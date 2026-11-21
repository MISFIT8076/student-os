"use client";

import { useRef, useEffect, useState } from "react";
import { sendChat } from "@/lib/api";

interface Msg {
  role: "user" | "assistant";
  text: string;
  time?: string;
  toolCalls?: { server: string; tool: string }[];
}

const GREEK_ORACLE_PROMPTS = [
  { label: "🔥 Top Priority", query: "What is my #1 priority right now?" },
  { label: "⏱️ Plan 2h Focus", query: "Plan a 2-hour deep focus study block for today" },
  { label: "💼 Internship Emails", query: "Are there any new internship or job emails?" },
  { label: "⑂ Review PRs", query: "Check my pending GitHub PRs and code reviews" },
  { label: "🎓 Exam Countdown", query: "Which exam is nearest and how should I prepare?" },
];

export default function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      text: "Greetings. I am the Oracle of Kairo. Inquire about your deadlines, coursework, code reviews, or let me synthesize the optimal sequence for your day.",
      time: "Now",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [messages, busy]);

  async function ask(text: string) {
    const q = text.trim();
    if (!q || busy) return;

    const timeStr = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    setMessages((m) => [...m, { role: "user", text: q, time: timeStr }]);
    setInput("");
    setBusy(true);

    try {
      const res = await sendChat(q);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: res.reply,
          toolCalls: res.tool_calls,
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: `Oracle connection disrupted: ${(e as Error).message}`,
          time: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  const clearChat = () => {
    setMessages([
      {
        role: "assistant",
        text: "The Oracle is cleared. How may Kairo guide your time now?",
        time: "Now",
      },
    ]);
  };

  return (
    <section className="panel chat-panel-container">
      {/* Header */}
      <div className="panel-head chat-header">
        <div className="oracle-title-wrap">
          <div className="oracle-avatar-badge">
            <span className="oracle-glyph">🏛️</span>
          </div>
          <div>
            <h2 className="oracle-name">Oracle of Kairo</h2>
            <p className="oracle-status-text small muted">
              <span className="live-status-dot" /> Autonomous Tool Intelligence
            </p>
          </div>
        </div>

        <button
          className="btn-ghost-sm"
          onClick={clearChat}
          title="Clear conversation"
          disabled={busy}
        >
          Clear
        </button>
      </div>

      {/* Chat Messages */}
      <div className="chat-log-box" ref={logRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-message-row ${m.role}`}>
            <div className="message-avatar">
              {m.role === "assistant" ? "Κ" : "You"}
            </div>
            <div className="message-bubble-body">
              <div className="message-text">
                {m.text.split("\n").map((line, j) => (
                  <span key={j}>
                    {line}
                    <br />
                  </span>
                ))}
              </div>

              {m.toolCalls && m.toolCalls.length > 0 && (
                <div className="tool-calls-pills small">
                  <span className="tool-calls-label">Invoked tools:</span>
                  {m.toolCalls.map((tc, idx) => (
                    <span key={idx} className="tool-pill">
                      {tc.server}/{tc.tool}
                    </span>
                  ))}
                </div>
              )}

              {m.time && <div className="message-time small muted">{m.time}</div>}
            </div>
          </div>
        ))}

        {busy && (
          <div className="chat-message-row assistant">
            <div className="message-avatar">Κ</div>
            <div className="message-bubble-body thinking-bubble">
              <div className="oracle-thinking-dots">
                <span />
                <span />
                <span />
              </div>
              <span className="small muted">Consulting your platforms…</span>
            </div>
          </div>
        )}
      </div>

      {/* Suggestions Chips */}
      <div className="oracle-prompts-bar">
        <div className="prompts-scroll">
          {GREEK_ORACLE_PROMPTS.map((p) => (
            <button
              key={p.label}
              className="oracle-prompt-chip"
              onClick={() => ask(p.query)}
              disabled={busy}
              title={p.query}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input Box */}
      <form
        className="chat-input-form"
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask the Oracle (e.g. 'What is due tonight?')"
          className="oracle-input-field"
          disabled={busy}
        />
        <button
          className="btn btn-primary oracle-send-btn"
          type="submit"
          disabled={busy || !input.trim()}
        >
          <span>Send</span>
          <span className="send-arrow">↵</span>
        </button>
      </form>
    </section>
  );
}
