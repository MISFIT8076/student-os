import type { Priority } from "@/lib/types";

const LABELS: Record<Priority, string> = {
  urgent: "Urgent",
  high: "High",
  medium: "Medium",
  low: "Low",
};

export default function PriorityBadge({ priority }: { priority: Priority }) {
  return <span className={`badge badge-${priority}`}>{LABELS[priority]}</span>;
}
