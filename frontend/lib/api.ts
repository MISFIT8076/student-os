import type { Briefing, ChatResponse, Progress, DaySchedule, OpportunityItem, ActionItem } from "./types";

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

export function getSchedule(): Promise<DaySchedule> {
  return json<DaySchedule>("/schedule");
}

export function getOpportunities(): Promise<OpportunityItem[]> {
  return json<OpportunityItem[]>("/opportunities");
}

export function updateOpportunityStatus(req: {
  source: string;
  title: string;
  due?: string | null;
  kind: string;
  otype: string;
  status: string;
}): Promise<{ ok: boolean }> {
  return json<{ ok: boolean }>("/opportunities/status", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function createTask(req: {
  title: string;
  detail?: string;
  due?: string | null;
  priority?: string;
  kind?: string;
  source?: string;
}): Promise<ActionItem> {
  return json<ActionItem>("/tasks", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function markTaskDone(req: {
  source: string;
  title: string;
  due?: string | null;
  kind?: string;
}): Promise<{ ok: boolean }> {
  return json<{ ok: boolean }>("/tasks/done", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function getTasks(): Promise<ActionItem[]> {
  return json<ActionItem[]>("/tasks");
}

export { API_BASE };
