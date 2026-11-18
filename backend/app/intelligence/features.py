"""Feature engineering for the learned ranker.

One `featurize()` used by BOTH training (on dataset rows) and runtime (on live
ActionItems), so there's no train/serve skew. Features are simple, named, and
mostly one-hot, which keeps a linear model interpretable — you can read off
which signals matter, which is great for the report.
"""
from __future__ import annotations

from collections.abc import Sequence

# Vocabularies (fixed so the feature vector is stable across train/serve).
KINDS = [
    "exam", "deadline", "pull_request", "contest", "email",
    "issue", "notification", "event", "practice", "announcement",
]
SOURCES = ["github", "gmail", "calendar", "codeforces", "classroom"]
CATEGORIES = ["internship", "academic", "otp", "other"]
DUE_BUCKETS = ["due_today", "due_tomorrow", "due_soon", "due_week", "due_far", "no_due"]

CONTEST_HINTS = ("contest", "codeforces", "leetcode", "hackathon", "round")


def _due_bucket(days_until: int | None) -> str:
    if days_until is None:
        return "no_due"
    if days_until <= 0:
        return "due_today"
    if days_until == 1:
        return "due_tomorrow"
    if days_until <= 3:
        return "due_soon"
    if days_until <= 7:
        return "due_week"
    return "due_far"


def is_contest(title: str, detail: str = "") -> bool:
    text = f"{title} {detail}".lower()
    return any(h in text for h in CONTEST_HINTS)


# The ordered feature names the model expects.
FEATURE_NAMES: list[str] = (
    [f"kind_{k}" for k in KINDS]
    + [f"src_{s}" for s in SOURCES]
    + [f"cat_{c}" for c in CATEGORIES]
    + [f"due_{b}" for b in DUE_BUCKETS]
    + ["exam_week", "is_contest", "contest_in_exam_week"]
)


def featurize(
    *,
    source: str,
    kind: str,
    days_until: int | None,
    category: str | None,
    title: str,
    detail: str = "",
    exam_week: bool = False,
) -> dict[str, float]:
    """Return a {feature_name: value} dict for one item."""
    contest = is_contest(title, detail)
    cat = category if category in CATEGORIES else "other"
    bucket = _due_bucket(days_until)

    feats = {name: 0.0 for name in FEATURE_NAMES}
    if f"kind_{kind}" in feats:
        feats[f"kind_{kind}"] = 1.0
    if f"src_{source}" in feats:
        feats[f"src_{source}"] = 1.0
    feats[f"cat_{cat}"] = 1.0
    feats[f"due_{bucket}"] = 1.0
    feats["exam_week"] = 1.0 if exam_week else 0.0
    feats["is_contest"] = 1.0 if contest else 0.0
    feats["contest_in_exam_week"] = 1.0 if (contest and exam_week) else 0.0
    return feats


def vectorize(feats: dict[str, float]) -> list[float]:
    """Turn a feature dict into an ordered vector matching FEATURE_NAMES."""
    return [feats.get(name, 0.0) for name in FEATURE_NAMES]


def vectorize_many(feat_dicts: Sequence[dict[str, float]]) -> list[list[float]]:
    return [vectorize(f) for f in feat_dicts]
