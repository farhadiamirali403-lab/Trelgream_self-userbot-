"""Automation (rule engine) models: rule -> conditions + actions."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, JSONType, TimestampMixin, int_pk


class AutomationRule(Base, TimestampMixin):
    __tablename__ = "automation_rules"

    id: Mapped[int] = int_pk()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)  # on_message, ...
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=0)
    execution_limit: Mapped[int | None] = mapped_column(Integer)

    conditions: Mapped[list["AutomationCondition"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", order_by="AutomationCondition.id"
    )
    actions: Mapped[list["AutomationAction"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", order_by="AutomationAction.sort_order"
    )


class AutomationCondition(Base):
    __tablename__ = "automation_conditions"

    id: Mapped[int] = int_pk()
    rule_id: Mapped[int] = mapped_column(ForeignKey("automation_rules.id", ondelete="CASCADE"), index=True)

    field: Mapped[str] = mapped_column(String(64), nullable=False)  # chat_id, text, sender_id
    operator: Mapped[str] = mapped_column(String(32), nullable=False)  # eq, contains, regex, ...
    value: Mapped[dict | None] = mapped_column(JSONType)
    logic: Mapped[str] = mapped_column(String(8), default="AND")  # AND / OR

    rule: Mapped["AutomationRule"] = relationship(back_populates="conditions")


class AutomationAction(Base):
    __tablename__ = "automation_actions"

    id: Mapped[int] = int_pk()
    rule_id: Mapped[int] = mapped_column(ForeignKey("automation_rules.id", ondelete="CASCADE"), index=True)

    action_type: Mapped[str] = mapped_column(String(64), nullable=False)  # reply, forward, ban
    payload: Mapped[dict | None] = mapped_column(JSONType)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    rule: Mapped["AutomationRule"] = relationship(back_populates="actions")
