"""Module registry: discovery and lookup of module classes."""

from __future__ import annotations

from app.modules.base import BaseModule


class ModuleRegistry:
    """Holds all known module classes, keyed by metadata.key."""

    def __init__(self) -> None:
        self._modules: dict[str, type[BaseModule]] = {}

    def register(self, module_cls: type[BaseModule]) -> None:
        key = module_cls.metadata.key
        if key in self._modules:
            raise ValueError(f"ماژول {key} قبلاً ثبت شده است")
        self._modules[key] = module_cls

    def discover(self, *module_classes: type[BaseModule]) -> None:
        for module_cls in module_classes:
            self.register(module_cls)

    def get(self, key: str) -> type[BaseModule] | None:
        return self._modules.get(key)

    def all(self) -> list[type[BaseModule]]:
        return list(self._modules.values())

    def metadata_list(self) -> list[dict]:
        return [
            {
                "key": cls.metadata.key,
                "name": cls.metadata.name,
                "category": cls.metadata.category,
                "version": cls.metadata.version,
                "description": cls.metadata.description,
                "permission": cls.metadata.permission,
                "default_enabled": cls.metadata.default_enabled,
                "is_core": cls.metadata.is_core,
            }
            for cls in self.all()
        ]


# Singleton registry for the application.
registry = ModuleRegistry()
