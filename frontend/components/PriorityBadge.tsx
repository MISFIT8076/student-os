import type { Priority } from "@/lib/types";

const PRIORITY_CONFIG: Record<
  Priority,
  { label: string; icon: string; className: string }
> = {
  urgent: { label: "Urgent", icon: "⚡", className: "badge-urgent" },
  high: { label: "High", icon: "▲", className: "badge-high" },
  medium: { label: "Medium", icon: "◆", className: "badge-medium" },
  low: { label: "Low", icon: "▽", className: "badge-low" },
};

export default function PriorityBadge({ priority }: { priority: Priority }) {
  const cfg = PRIORITY_CONFIG[priority] ?? PRIORITY_CONFIG.medium;
  return (
    <span className={`badge ${cfg.className}`}>
      <span className="badge-icon">{cfg.icon}</span>
      <span>{cfg.label}</span>
    </span>
  );
}
