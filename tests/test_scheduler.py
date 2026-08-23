"""Scheduler repeat-rule tests."""

from __future__ import annotations

from datetime import datetime, timezone

from app.scheduler.service import next_run_after


def _dt() -> datetime:
    return datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)


def test_one_time():
    assert next_run_after(_dt(), "one_time") is None


def test_daily():
    assert next_run_after(_dt(), "daily").day == 2


def test_weekly():
    assert next_run_after(_dt(), "weekly").day == 8


def test_hourly():
    assert next_run_after(_dt(), "hourly").hour == 11


def test_interval():
    assert next_run_after(_dt(), "interval:3600").hour == 11


def test_unknown_returns_none():
    assert next_run_after(_dt(), "unknown_rule") is None
