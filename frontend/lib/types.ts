// Mirrors backend/app/schemas.py

export type Priority = "urgent" | "high" | "medium" | "low";

export interface ActionItem {
  source: string;
  kind: string;
  title: string;
  detail: string;
  url?: string | null;
  due?: string | null;
  priority: Priority;
  score: number;
  raw: Record<string, unknown>;
}

export interface Briefing {
  generated_at: string;
  headline: string;
  summary: string;
  items: ActionItem[];
  sources_used: string[];
  llm_used: boolean;
  cached: boolean;
}

export interface ChatResponse {
  reply: string;
  tool_calls: { server: string; tool: string }[];
  llm_used: boolean;
}

export interface Progress {
  items_shown: number;
  actions: Record<string, number>;
  total_actions: number;
  done_streak_days: number;
  active_days: number;
  application_funnel: Record<string, number>;
}

export interface ScheduleBlock {
  start: string;
  end: string;
  minutes: number;
  title: string;
  source: string;
  kind: string;
  due?: string | null;
  priority: string;
}

export interface ScheduleOverflow {
  title: string;
  source: string;
  kind: string;
  due?: string | null;
  minutes: number;
}

export interface DaySchedule {
  date: string;
  blocks: ScheduleBlock[];
  overflow: ScheduleOverflow[];
  available_minutes: number;
  demand_minutes: number;
  scheduled_minutes: number;
  overcommitted: boolean;
  advice: string;
}

export interface OpportunityItem {
  key: string;
  type: "contest" | "internship" | "scholarship" | "project" | string;
  title: string;
  detail: string;
  source: string;
  kind: string;
  due?: string | null;
  url?: string | null;
  status: "new" | "saved" | "applied" | "interviewing" | "accepted" | "rejected" | string;
}
