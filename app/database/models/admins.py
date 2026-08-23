"""Admin, role and permission models (RBAC)."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, int_pk


class Admin(Base, TimestampMixin):
    __tablename__ = "admins"

    id: Mapped[int] = int_pk()
    telegram_id: Mapped[int] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        secondary="admin_roles", back_populates="admins", lazy="selectin"
    )


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[int] = int_pk()
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)  # OWNER/ADMIN/...
    description: Mapped[str | None] = mapped_column(String(255))

    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions", back_populates="roles", lazy="selectin"
    )
    admins: Mapped[list["Admin"]] = relationship(
        secondary="admin_roles", back_populates="roles", lazy="selectin"
    )


class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id: Mapped[int] = int_pk()
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)  # users.view
    description: Mapped[str | None] = mapped_column(String(255))

    roles: Mapped[list["Role"]] = relationship(
        secondary="role_permissions", back_populates="permissions", lazy="selectin"
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


class AdminRole(Base):
    __tablename__ = "admin_roles"

    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
