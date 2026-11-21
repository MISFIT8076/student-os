import type {
  Briefing,
  ChatResponse,
  Progress,
  DaySchedule,
  OpportunityItem,
  User,
  AuthResponse,
  ConnectionOut,
  ConnectionTestResult,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

const TOKEN_KEY = "kairo_access_token";
const USER_KEY = "kairo_user_profile";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setStoredUser(user: User | null): void {
  if (typeof window === "undefined") return;
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_KEY);
  }
}

export function clearAuth(): void {
  setStoredToken(null);
  setStoredUser(null);
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((init?.headers as Record<string, string>) ?? {}),
  };

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (!res.ok) {
    let errMsg = `${path} failed: ${res.status} ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errMsg = errJson.detail;
    } catch {}
    throw new Error(errMsg);
  }
  return res.json() as Promise<T>;
}

// ── Auth Endpoints ──────────────────────────────────────────────────────────
export async function registerUser(req: {
  email: string;
  name: string;
  password: string;
}): Promise<AuthResponse> {
  const data = await json<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(req),
  });
  setStoredToken(data.access_token);
  setStoredUser(data.user);
  return data;
}

export async function loginUser(req: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  const data = await json<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(req),
  });
  setStoredToken(data.access_token);
  setStoredUser(data.user);
  return data;
}

export async function getGoogleClientId(): Promise<string> {
  try {
    const data = await json<{ client_id: string }>("/api/auth/google/client-id");
    return data.client_id || "";
  } catch {
    return "";
  }
}

export async function googleLogin(req: {
  email?: string;
  name?: string;
  google_id?: string;
  avatar_url?: string;
  credential?: string;
}): Promise<AuthResponse> {
  const data = await json<AuthResponse>("/api/auth/google", {
    method: "POST",
    body: JSON.stringify(req),
  });
  setStoredToken(data.access_token);
  setStoredUser(data.user);
  return data;
}

export async function getMe(): Promise<User> {
  const user = await json<User>("/api/auth/me");
  setStoredUser(user);
  return user;
}

// ── Connections Endpoints ───────────────────────────────────────────────────
export function getConnections(): Promise<ConnectionOut[]> {
  return json<ConnectionOut[]>("/api/connections");
}

export function exchangeGoogleCode(
  code: string,
  redirect_uri?: string
): Promise<ConnectionTestResult> {
  return json<ConnectionTestResult>("/api/connections/google/exchange-code", {
    method: "POST",
    body: JSON.stringify({ code, redirect_uri }),
  });
}

export function saveConnection(
  provider: string,
  credentials: Record<string, any>
): Promise<ConnectionTestResult> {
  return json<ConnectionTestResult>(`/api/connections/${provider}`, {
    method: "POST",
    body: JSON.stringify({ credentials }),
  });
}

export function testConnection(
  provider: string,
  credentials: Record<string, any>
): Promise<ConnectionTestResult> {
  return json<ConnectionTestResult>(`/api/connections/${provider}/test`, {
    method: "POST",
    body: JSON.stringify({ credentials }),
  });
}

export function disconnectConnection(
  provider: string
): Promise<{ provider: string; disconnected: boolean }> {
  return json<{ provider: string; disconnected: boolean }>(
    `/api/connections/${provider}`,
    {
      method: "DELETE",
    }
  );
}

// ── Existing Endpoints ──────────────────────────────────────────────────────
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

export { API_BASE };

