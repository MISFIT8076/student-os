"use client";

import { useState } from "react";
import type { ActionItem, Priority } from "@/lib/types";
import { createTask } from "@/lib/api";

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (item: ActionItem) => void;
}

const PRESET_KINDS = [
  { id: "deadline", label: "⏰ Deadline" },
  { id: "assignment", label: "📝 Assignment" },
  { id: "exam", label: "🎓 Exam" },
  { id: "project", label: "💻 Project" },
  { id: "practice", label: "⚔ Practice" },
  { id: "contest", label: "🏆 Contest" },
];

const PRESET_SOURCES = [
  { id: "personal", label: "Personal" },
  { id: "college", label: "College / Uni" },
  { id: "classroom", label: "Classroom" },
  { id: "github", label: "GitHub" },
  { id: "codeforces", label: "Codeforces" },
];

export default function CreateTaskModal({
  isOpen,
  onClose,
  onCreated,
}: CreateTaskModalProps) {
  const [title, setTitle] = useState("");
  const [detail, setDetail] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");
  const [kind, setKind] = useState("deadline");
  const [source, setSource] = useState("personal");
  const [due, setDue] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Please provide a task title.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const created = await createTask({
        title: title.trim(),
        detail: detail.trim(),
        priority,
        kind,
        source,
        due: due ? due : null,
      });

      onCreated(created);
      onClose();
      // Reset form
      setTitle("");
      setDetail("");
      setPriority("medium");
      setKind("deadline");
      setDue("");
    } catch (err) {
      // Fallback: create client-side ActionItem even if backend is temporarily unreachable
      const scoreMap: Record<Priority, number> = {
        urgent: 10.0,
        high: 7.0,
        medium: 4.0,
        low: 1.5,
      };
      const fallbackItem: ActionItem = {
        source,
        kind,
        title: title.trim(),
        detail: detail.trim(),
        due: due ? due : null,
        priority,
        score: scoreMap[priority] || 4.0,
        raw: { is_custom: true },
      };
      onCreated(fallbackItem);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="task-modal-overlay" onClick={onClose}>
      <div
        className="task-modal-glass-card"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="task-modal-header">
          <div className="task-modal-title-group">
            <span className="task-modal-sparkle">✦</span>
            <h2 className="task-modal-title">Create Action Item</h2>
          </div>
          <button
            className="task-modal-close-btn"
            onClick={onClose}
            type="button"
          >
            ✕
          </button>
        </div>

        <p className="task-modal-subtitle">
          Define your prioritized tasks, coursework milestones, or study goals.
        </p>

        {error && <div className="alert task-alert-error">{error}</div>}

        <form onSubmit={handleSubmit} className="task-modal-form">
          {/* Title */}
          <div className="form-group">
            <label className="form-label" htmlFor="task-title">
              Task Title <span className="text-urgent">*</span>
            </label>
            <input
              id="task-title"
              type="text"
              className="kairo-input"
              placeholder="e.g. Operating Systems Assignment 5 Submission..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              autoFocus
            />
          </div>

          {/* Priority Selection */}
          <div className="form-group">
            <label className="form-label">Priority Level</label>
            <div className="priority-select-row">
              <button
                type="button"
                className={`priority-chip-btn chip-urgent ${
                  priority === "urgent" ? "active" : ""
                }`}
                onClick={() => setPriority("urgent")}
              >
                <span className="chip-dot dot-urgent" />
                <span>Urgent</span>
              </button>

              <button
                type="button"
                className={`priority-chip-btn chip-high ${
                  priority === "high" ? "active" : ""
                }`}
                onClick={() => setPriority("high")}
              >
                <span className="chip-dot dot-high" />
                <span>High</span>
              </button>

              <button
                type="button"
                className={`priority-chip-btn chip-medium ${
                  priority === "medium" ? "active" : ""
                }`}
                onClick={() => setPriority("medium")}
              >
                <span className="chip-dot dot-medium" />
                <span>Medium</span>
              </button>

              <button
                type="button"
                className={`priority-chip-btn chip-low ${
                  priority === "low" ? "active" : ""
                }`}
                onClick={() => setPriority("low")}
              >
                <span className="chip-dot dot-low" />
                <span>Low</span>
              </button>
            </div>
          </div>

          {/* Kind / Category Selection */}
          <div className="form-group">
            <label className="form-label">Category</label>
            <div className="kind-select-row">
              {PRESET_KINDS.map((k) => (
                <button
                  key={k.id}
                  type="button"
                  className={`kind-chip-btn ${kind === k.id ? "active" : ""}`}
                  onClick={() => setKind(k.id)}
                >
                  {k.label}
                </button>
              ))}
            </div>
          </div>

          {/* Two Columns: Source & Due Date */}
          <div className="form-row-2col">
            <div className="form-group">
              <label className="form-label">Origin / Scope</label>
              <select
                className="kairo-select"
                value={source}
                onChange={(e) => setSource(e.target.value)}
              >
                {PRESET_SOURCES.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Due Date (Optional)</label>
              <input
                type="date"
                className="kairo-input"
                value={due}
                onChange={(e) => setDue(e.target.value)}
              />
            </div>
          </div>

          {/* Detail / Notes */}
          <div className="form-group">
            <label className="form-label" htmlFor="task-detail">
              Details / Instructions (Optional)
            </label>
            <textarea
              id="task-detail"
              className="kairo-textarea"
              rows={2}
              placeholder="Add checklist, syllabus units, or deliverables..."
              value={detail}
              onChange={(e) => setDetail(e.target.value)}
            />
          </div>

          {/* Footer Controls */}
          <div className="task-modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary task-btn-create"
              disabled={loading || !title.trim()}
            >
              {loading ? "Creating..." : "✦ Create Action Item"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
