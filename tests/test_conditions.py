"""Automation condition engine tests."""

from __future__ import annotations

from types import SimpleNamespace

from app.automation.conditions import evaluate_all, evaluate_condition

CTX = {"text": "سلام دنیا", "chat_id": 123, "sender_id": 456, "is_private": False, "media_type": None}


def test_eq():
    assert evaluate_condition("chat_id", "eq", 123, CTX)


def test_contains():
    assert evaluate_condition("text", "contains", "سلام", CTX)
    assert not evaluate_condition("text", "contains", "خداحافظ", CTX)


def test_regex():
    assert evaluate_condition("text", "regex", r"^سلام", CTX)


def test_gt():
    assert evaluate_condition("chat_id", "gt", 100, CTX)


def test_in():
    assert evaluate_condition("sender_id", "in", [456, 789], CTX)


def test_exists():
    assert evaluate_condition("media_type", "exists", None, CTX) is False


def test_evaluate_all_and():
    conds = [
        SimpleNamespace(field="text", operator="contains", value={"value": "سلام"}, logic="AND"),
        SimpleNamespace(field="chat_id", operator="eq", value={"value": 123}, logic="AND"),
    ]
    assert evaluate_all(conds, CTX) is True


def test_evaluate_all_or_false():
    conds = [
        SimpleNamespace(field="text", operator="contains", value={"value": "xx"}, logic="AND"),
        SimpleNamespace(field="chat_id", operator="eq", value={"value": 999}, logic="OR"),
    ]
    assert evaluate_all(conds, CTX) is False


def test_evaluate_all_empty():
    assert evaluate_all([], CTX) is True
