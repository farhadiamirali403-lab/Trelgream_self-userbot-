"""Module registry and per-user module state models."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, JSONType, TimestampMixin, int_pk


class Module(Base, TimestampMixin):
    __tablename__ = "modules"

    id: Mapped[int] = int_pk()
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # auto_reply
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="general")
    version: Mapped[str] = mapped_column(String(16), default="1.0.0")
    description: Mapped[str | None] = mapped_column(Text)

    is_core: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Optional module metadata (permission code, dependencies, config schema).
    meta: Mapped[dict | None] = mapped_column(JSONType)

    user_instances: Mapped[list["UserModule"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )


class UserModule(Base, TimestampMixin):
    __tablename__ = "user_modules"
    __table_args__ = (UniqueConstraint("user_id", "module_id", name="uq_user_module"),)

    id: Mapped[int] = int_pk()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"))

    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    module: Mapped["Module"] = relationship(back_populates="user_instances", lazy="selectin")
    settings: Mapped[list["ModuleSetting"]] = relationship(
        back_populates="user_module", cascade="all, delete-orphan"
    )


class ModuleSetting(Base, TimestampMixin):
    __tablename__ = "module_settings"
    __table_args__ = (UniqueConstraint("user_module_id", "key", name="uq_module_setting"),)

    id: Mapped[int] = int_pk()
    user_module_id: Mapped[int] = mapped_column(
        ForeignKey("user_modules.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[dict | None] = mapped_column(JSONType)

    user_module: Mapped["UserModule"] = relationship(back_populates="settings")
