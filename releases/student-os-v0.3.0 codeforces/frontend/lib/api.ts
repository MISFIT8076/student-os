import type { Briefing, ChatResponse, Progress } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function getBriefing(refresh = false): Promise<Briefing> {
  return json<Briefing>(`/briefing${refresh ? "?refresh=true" : ""}`);
}

export function sendChat(message: string): Promise<ChatResponse> {
  return json<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function getProgress(): Promise<Progress> {
  return json<Progress>("/progress");
}

export { API_BASE };
