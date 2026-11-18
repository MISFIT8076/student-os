"""Tests for deadline extraction."""
from __future__ import annotations

from datetime import date

from mcp_servers.common.extraction import enrich_due, extract_due
from eval.extraction_eval import run as run_extraction_eval

REF = date(2026, 8, 3)  # a fixed Monday-ish reference


def test_relative_dates():
    assert extract_due("submit by today", REF) == "2026-08-03"
    assert extract_due("closes tomorrow", REF) == "2026-08-04"
    assert extract_due("deadline day after tomorrow", REF) == "2026-08-05"
    assert extract_due("apply in 3 days", REF) == "2026-08-06"


def test_absolute_dates():
    assert extract_due("last date is 10 August", REF) == "2026-08-10"
    assert extract_due("submit before August 6", REF) == "2026-08-06"
    assert extract_due("fee due by 05/08", REF) == "2026-08-05"


def test_weekday_resolves_to_future_occurrence():
    got = extract_due("apply by Friday", REF)
    assert got is not None
    assert date.fromisoformat(got).weekday() == 4  # Friday
    assert date.fromisoformat(got) >= REF


def test_negatives_return_none():
    assert extract_due("Your OTP is 4821, valid 10 minutes", REF) is None
    assert extract_due("Flat 50% off this week!", REF) is None
    assert extract_due("Weekly newsletter digest", REF) is None


def test_enrich_due_marks_source():
    items = [{"title": "Scholarship — apply by tomorrow", "detail": "", "due": None, "extra": {}}]
    enrich_due(items, REF)
    assert items[0]["due"] == "2026-08-04"
    assert items[0]["extra"]["due_source"] == "extracted"


def test_enrich_does_not_overwrite_existing_due():
    items = [{"title": "already dated", "detail": "", "due": "2026-08-01", "extra": {}}]
    enrich_due(items, REF)
    assert items[0]["due"] == "2026-08-01"


def test_extraction_eval_quality():
    r = run_extraction_eval()
    assert r["f1"] >= 0.85  # strong extraction on the labeled set
