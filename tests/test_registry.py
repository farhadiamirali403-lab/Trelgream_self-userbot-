"""Module registry integrity tests."""

from __future__ import annotations

import app.modules.builtin  # noqa: F401  (registers modules)
from app.modules.registry import registry


def test_all_keys_unique():
    keys = [c.metadata.key for c in registry.all()]
    assert len(keys) == len(set(keys)), "کلیدهای ماژول تکراری هستند"


def test_implemented_count():
    impl = [c for c in registry.all() if not c.metadata.not_implemented]
    assert len(impl) >= 40, "تعداد ماژول‌های پیاده‌سازی‌شده کافی نیست"


def test_catalog_has_categories():
    from app.modules.builtin.catalog import CATEGORY_NAMES

    assert "entertainment" in CATEGORY_NAMES
    assert "market" in CATEGORY_NAMES


def test_no_duplicate_declared():
    declared = [c.metadata.key for c in registry.all() if c.metadata.not_implemented]
    impl = [c.metadata.key for c in registry.all() if not c.metadata.not_implemented]
    assert not (set(declared) & set(impl)), "ماژولی هم پیاده و هم اعلام‌شده است"
