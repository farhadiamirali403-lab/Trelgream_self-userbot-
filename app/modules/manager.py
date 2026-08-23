"""Module manager service: enable/disable/settings with plan-limit checks."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.repositories import SubscriptionRepository
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.database.models.modules import Module, ModuleSetting, UserModule


class ModuleManager:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_module(self, key: str, name: str, category: str, **meta) -> Module:
        stmt = select(Module).where(Module.key == key)
        result = await self.session.execute(stmt)
        module = result.scalar_one_or_none()
        if module is None:
            module = Module(key=key, name=name, category=category, **meta)
            self.session.add(module)
            await self.session.flush()
        return module

    async def enable(self, user_id: int, module_id: int) -> UserModule:
        await self._check_limit(user_id)
        stmt = select(UserModule).where(
            UserModule.user_id == user_id, UserModule.module_id == module_id
        )
        result = await self.session.execute(stmt)
        um = result.scalar_one_or_none()
        if um is None:
            um = UserModule(user_id=user_id, module_id=module_id, enabled=True)
            self.session.add(um)
        else:
            um.enabled = True
        await self.session.flush()
        return um

    async def disable(self, user_id: int, module_id: int) -> UserModule:
        stmt = select(UserModule).where(
            UserModule.user_id == user_id, UserModule.module_id == module_id
        )
        result = await self.session.execute(stmt)
        um = result.scalar_one_or_none()
        if um is None:
            raise NotFoundError("این ماژول فعال نیست")
        um.enabled = False
        await self.session.flush()
        return um

    async def set_setting(self, user_id: int, module_id: int, key: str, value: dict) -> ModuleSetting:
        stmt = select(UserModule).where(
            UserModule.user_id == user_id, UserModule.module_id == module_id
        )
        result = await self.session.execute(stmt)
        um = result.scalar_one_or_none()
        if um is None or not um.enabled:
            raise ConflictError("ابتدا ماژول را فعال کنید")

        stmt2 = select(ModuleSetting).where(
            ModuleSetting.user_module_id == um.id, ModuleSetting.key == key
        )
        r2 = await self.session.execute(stmt2)
        setting = r2.scalar_one_or_none()
        if setting is None:
            setting = ModuleSetting(user_module_id=um.id, key=key, value=value)
            self.session.add(setting)
        else:
            setting.value = value
        await self.session.flush()
        return setting

    async def settings_for(self, user_id: int, module_id: int) -> dict[str, dict]:
        stmt = (
            select(ModuleSetting)
            .join(UserModule, UserModule.id == ModuleSetting.user_module_id)
            .where(UserModule.user_id == user_id, UserModule.module_id == module_id)
        )
        result = await self.session.execute(stmt)
        return {s.key: s.value for s in result.scalars().all()}

    async def _check_limit(self, user_id: int) -> None:
        subs = SubscriptionRepository(self.session)
        active = await subs.active_for_user(user_id)
        if active is None or active.plan is None:
            raise PermissionDeniedError("اشتراک فعال برای فعال‌سازی ماژول لازم است")
        enabled_count = await self._enabled_count(user_id)
        max_modules = active.plan.max_modules
        if enabled_count >= max_modules:
            raise ConflictError(f"سقف ماژول‌های پلن ({max_modules}) پر شده است")

    async def _enabled_count(self, user_id: int) -> int:
        stmt = select(UserModule).where(
            UserModule.user_id == user_id, UserModule.enabled.is_(True)
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())
