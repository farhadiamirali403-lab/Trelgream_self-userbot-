"""Condition evaluation for the automation engine."""

from __future__ import annotations

import re
from typing import Any


def _as_str(value: Any) -> str:
    return "" if value is None else str(value)


def evaluate_condition(field: str, operator: str, value: Any, context: dict) -> bool:
    """Evaluate a single condition against an event context."""
    actual = context.get(field)
    expected = value if not isinstance(value, dict) else value.get("value")

    if operator == "exists":
        return actual is not None
    if operator == "not_exists":
        return actual is None

    if actual is None:
        return False

    try:
        if operator == "eq":
            return actual == expected
        if operator == "neq":
            return actual != expected
        if operator == "contains":
            return str(expected) in _as_str(actual)
        if operator == "not_contains":
            return str(expected) not in _as_str(actual)
        if operator == "startswith":
            return _as_str(actual).startswith(str(expected))
        if operator == "endswith":
            return _as_str(actual).endswith(str(expected))
        if operator == "regex":
            return re.search(str(expected), _as_str(actual)) is not None
        if operator == "gt":
            return float(actual) > float(expected)
        if operator == "lt":
            return float(actual) < float(expected)
        if operator == "gte":
            return float(actual) >= float(expected)
        if operator == "lte":
            return float(actual) <= float(expected)
        if operator == "in":
            return actual in (expected if isinstance(expected, (list, tuple, set)) else [expected])
        if operator == "not_in":
            return actual not in (expected if isinstance(expected, (list, tuple, set)) else [expected])
    except (TypeError, ValueError):
        return False
    return False


def evaluate_all(conditions: list, context: dict) -> bool:
    """Evaluate conditions honoring AND/OR logic (OR groups by precedence)."""
    if not conditions:
        return True
    # Group into OR-clauses separated by AND logic.
    result: bool | None = None
    current_or = False
    for cond in conditions:
        this = evaluate_condition(cond.field, cond.operator, cond.value, context)
        logic = (cond.logic or "AND").upper()
        if result is None:
            result = this
            current_or = this
        elif logic == "OR":
            result = result or this
        else:  # AND
            result = result and this
    return bool(result)
