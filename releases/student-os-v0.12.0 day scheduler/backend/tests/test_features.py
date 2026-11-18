"""Tests for the feature builder (shared by training and serving)."""
from __future__ import annotations

from app.intelligence.features import FEATURE_NAMES, featurize, is_contest, vectorize


def test_vector_length_matches_names():
    f = featurize(source="gmail", kind="email", days_until=2,
                  category="internship", title="Apply now")
    assert len(vectorize(f)) == len(FEATURE_NAMES)


def test_one_hots_set_correctly():
    f = featurize(source="calendar", kind="exam", days_until=0,
                  category=None, title="OS exam", exam_week=True)
    assert f["kind_exam"] == 1.0
    assert f["src_calendar"] == 1.0
    assert f["due_due_today"] == 1.0
    assert f["cat_other"] == 1.0  # unknown/None category maps to 'other'
    assert f["exam_week"] == 1.0


def test_no_due_bucket():
    f = featurize(source="github", kind="pull_request", days_until=None,
                  category=None, title="PR: review requested")
    assert f["due_no_due"] == 1.0


def test_contest_detection_and_interaction():
    f = featurize(source="codeforces", kind="contest", days_until=0,
                  category=None, title="Codeforces Round", exam_week=True)
    assert is_contest("Codeforces Round")
    assert f["is_contest"] == 1.0
    assert f["contest_in_exam_week"] == 1.0
