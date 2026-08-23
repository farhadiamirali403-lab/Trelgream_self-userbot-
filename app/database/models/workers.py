"""Worker and heartbeat models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, int_pk


class Worker(Base, TimestampMixin):
    __tablename__ = "workers"

    id: Mapped[int] = int_pk()
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    host: Mapped[str] = mapped_column(String(128), default="localhost")
    pid: Mapped[int | None] = mapped_column(Integer)

    # STARTING/RUNNING/STOPPING/STOPPED/ERROR/RECOVERING
    status: Mapped[str] = mapped_column(String(32), default="STARTING", nullable=False)
    load: Mapped[float] = mapped_column(Float, default=0.0)
    capacity: Mapped[int] = mapped_column(Integer, default=10)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    userbots: Mapped[list["Userbot"]] = relationship(back_populates="worker")  # noqa: F821
    heartbeats: Mapped[list["WorkerHeartbeat"]] = relationship(
        back_populates="worker", cascade="all, delete-orphan"
    )


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"

    id: Mapped[int] = int_pk()
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id", ondelete="CASCADE"), index=True)

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cpu: Mapped[float | None] = mapped_column(Float)
    ram: Mapped[float | None] = mapped_column(Float)
    active_userbots: Mapped[int] = mapped_column(Integer, default=0)

    worker: Mapped["Worker"] = relationship(back_populates="heartbeats")
