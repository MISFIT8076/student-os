"use client";

import { useState } from "react";
import { sendChat } from "@/lib/api";

interface Msg {
  role: "user" | "assistant";
  text: string;
}

const SUGGESTIONS = [
  "What should I do today?",
  "Show my GitHub PRs",
  "Any internship emails?",
  "What deadlines are coming up?",
];

export default function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function ask(text: string) {
    const q = text.trim();
    if (!q || busy) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setBusy(true);
    try {
      const res = await sendChat(q);
      setMessages((m) => [...m, { role: "assistant", text: res.reply }]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `Error: ${(e as Error).message}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel chat">
      <div className="panel-head">
        <h2>Ask Student OS</h2>
      </div>

      <div className="chat-log">
        {messages.length === 0 && (
          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="chip" onClick={() => ask(s)}>
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.text.split("\n").map((line, j) => (
              <span key={j}>
                {line}
                <br />
              </span>
            ))}
          </div>
        ))}
        {busy && <div className="bubble assistant muted">Thinking…</div>}
      </div>

      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your day, emails, PRs, deadlines…"
        />
        <button className="btn" type="submit" disabled={busy}>
          Send
        </button>
      </form>
    </section>
  );
}
