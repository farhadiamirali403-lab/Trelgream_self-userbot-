"""Worker manager: supervises userbots (start/stop/restart/heartbeat/recovery)."""

from __future__ import annotations

import asyncio
import os
import socket
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from telethon import events

from app.automation.service import AutomationService
from app.core.config import Settings
from app.core.logging import get_logger
from app.core.security import SessionCipher
from app.database.models.modules import UserModule
from app.database.models.userbots import Userbot
from app.database.models.workers import Worker
from app.database.session import async_session_factory
from app.modules.registry import ModuleRegistry
from app.scheduler.queue import TaskQueue
from app.telegram.client_factory import build_user_client
from app.userbots.repository import UserbotRepository
from app.userbots.runtime import UserbotRuntime
from app.workers.commands import CommandBus

log = get_logger("workers.manager")


def _now() -> datetime:
    return datetime.now(timezone.utc)


class WorkerManager:
    """Supervisor that owns a set of userbot runtimes in one process."""

    def __init__(
        self,
        settings: Settings,
        cipher: SessionCipher,
        command_bus: CommandBus,
        registry: ModuleRegistry,
        task_queue: TaskQueue | None = None,
        worker_name: str = "W-01",
    ) -> None:
        self.settings = settings
        self.cipher = cipher
        self.command_bus = command_bus
        self.registry = registry
        self.task_queue = task_queue
        self.worker_name = worker_name
        self.runtimes: dict[int, UserbotRuntime] = {}
        self.tasks: dict[int, asyncio.Task] = {}
        self.retry_counts: dict[int, int] = {}
        self._stop = asyncio.Event()

    async def run(self) -> None:
        """Main supervisor loop."""
        log.info("WorkerManager starting", extra_fields={"worker": self.worker_name})
        while not self._stop.is_set():
            async with async_session_factory() as session:
                try:
                    await self._heartbeat(session)
                    await self._process_commands(session)
                    await self._process_tasks()
                    await self._sync(session)
                    await session.commit()
                except Exception as exc:  # noqa: BLE001
                    await session.rollback()
                    log.error("supervisor iteration failed", extra_fields={"error": str(exc)})
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.settings.worker_heartbeat_interval)
            except asyncio.TimeoutError:
                pass
        await self.shutdown()

    async def shutdown(self) -> None:
        log.info("WorkerManager shutting down")
        for uid in list(self.tasks):
            await self._stop_userbot(uid)
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)

    # --- supervision ---

    async def _sync(self, session) -> None:
        repo = UserbotRepository(session)
        runnable = await repo.list_runnable()
        wanted = {u.id for u in runnable}

        # Stop userbots that should no longer run.
        for uid in list(self.tasks):
            if uid not in wanted:
                await self._stop_userbot(uid)

        # Start missing userbots.
        for userbot in runnable:
            if userbot.id not in self.tasks:
                await self._start_userbot(session, userbot)

    async def _start_userbot(self, session, userbot: Userbot) -> None:
        try:
            session_str = await UserbotRepository(session).get_active_session(
                userbot.telegram_account_id, self.cipher
            )
            module_classes, module_settings = await self._load_modules(session, userbot.user_id)
            client = build_user_client(session_str, self.settings)
            runtime = UserbotRuntime(
                user_id=userbot.user_id,
                userbot_id=userbot.id,
                client=client,
                registry=self.registry,
                module_classes=module_classes,
                module_settings=module_settings,
                command_bus=self.command_bus,
            )
            self.runtimes[userbot.id] = runtime
            task = asyncio.create_task(self._run_userbot(userbot, runtime))
            self.tasks[userbot.id] = task
            userbot.status = "STARTING"
            userbot.current_worker_id = None
            userbot.error_message = None
            log.info("starting userbot", extra_fields={"userbot_id": userbot.id})
        except Exception as exc:  # noqa: BLE001
            userbot.status = "ERROR"
            userbot.error_message = str(exc)[:500]
            log.error("start failed", extra_fields={"userbot_id": userbot.id, "error": str(exc)})

    async def _run_userbot(self, userbot: Userbot, runtime: UserbotRuntime) -> None:
        try:
            await runtime.start()
            runtime.client.add_event_handler(
                lambda event: self._on_automation_event(userbot, runtime, event),
                events.NewMessage(incoming=True),
            )
            await self._set_status(userbot.id, "RUNNING")
            log.info("userbot running", extra_fields={"userbot_id": userbot.id})
            await runtime.client.run_until_disconnected()
            await self._set_status(userbot.id, "STOPPED")
        except Exception as exc:  # noqa: BLE001
            await self._set_status(userbot.id, "ERROR", error=str(exc)[:500])
            self.retry_counts[userbot.id] = self.retry_counts.get(userbot.id, 0) + 1
            delay = min(2 ** self.retry_counts[userbot.id], 300)
            log.warning(
                "userbot crashed; recovery backoff",
                extra_fields={"userbot_id": userbot.id, "delay": delay, "error": str(exc)},
            )
            await asyncio.sleep(delay)
            await self._set_status(userbot.id, "RECOVERING")
        finally:
            self.tasks.pop(userbot.id, None)
            self.runtimes.pop(userbot.id, None)

    async def _on_automation_event(self, userbot: Userbot, runtime: UserbotRuntime, event) -> None:
        try:
            async with async_session_factory() as session:
                await AutomationService(session).handle_event(
                    userbot.user_id, "new_message", runtime.client, event
                )
        except Exception as exc:  # noqa: BLE001
            log.error("automation failed", extra_fields={"userbot_id": userbot.id, "error": str(exc)})

    async def _process_tasks(self) -> None:
        if self.task_queue is None:
            return
        while True:
            task = await self.task_queue.pop()
            if task is None:
                break
            try:
                await self._execute_task(task)
            except Exception as exc:  # noqa: BLE001
                log.error("task execution failed", extra_fields={"task_id": task.get("task_id"), "error": str(exc)})

    async def _execute_task(self, task: dict) -> None:
        user_id = int(task.get("user_id", 0))
        payload = task.get("payload") or {}
        runtime = next((r for r in self.runtimes.values() if r.user_id == user_id), None)
        if runtime is None:
            log.warning("no runtime for task", extra_fields={"user_id": user_id})
            return
        type_ = task.get("type")
        if type_ == "send_message":
            peer = payload.get("peer")
            text = payload.get("text", "")
            if peer:
                await runtime.client.send_message(peer, text)
        else:
            log.warning("unknown task type", extra_fields={"type": type_})

    async def _stop_userbot(self, uid: int) -> None:
        runtime = self.runtimes.get(uid)
        task = self.tasks.get(uid)
        if runtime is not None:
            await runtime.client.disconnect()
        if task is not None and not task.done():
            try:
                await asyncio.wait_for(task, timeout=10)
            except (asyncio.TimeoutError, Exception):  # noqa: BLE001
                task.cancel()

    async def _process_commands(self, session) -> None:
        while True:
            command = await self.command_bus.pop()
            if command is None:
                break
            action = command.get("action")
            target = int(command.get("target_id", 0))
            log.info(
                "received command",
                extra_fields={"action": action, "target": target, "command_id": command.get("command_id")},
            )
            if action == "start":
                await self._handle_start(session, target)
            elif action == "stop":
                await self._handle_stop(session, target)
            elif action == "restart":
                await self._handle_stop(session, target)
                await self._handle_start(session, target)

    async def _handle_start(self, session, target: int) -> None:
        repo = UserbotRepository(session)
        userbot = await repo.get(target)
        if userbot is not None:
            userbot.status = "STARTING"
            self.retry_counts.pop(target, None)

    async def _handle_stop(self, session, target: int) -> None:
        repo = UserbotRepository(session)
        userbot = await repo.get(target)
        if userbot is not None:
            userbot.status = "STOPPED"
        await self._stop_userbot(target)

    async def _heartbeat(self, session) -> None:
        stmt = select(Worker).where(Worker.name == self.worker_name)
        result = await session.execute(stmt)
        worker = result.scalar_one_or_none()
        if worker is None:
            worker = Worker(
                name=self.worker_name,
                host=socket.gethostname(),
                pid=os.getpid(),
                status="RUNNING",
                started_at=_now(),
            )
            session.add(worker)
        worker.status = "RUNNING"
        worker.last_heartbeat_at = _now()
        worker.load = len(self.tasks)
        worker.pid = os.getpid()
        # Update owning userbot heartbeat pointers.
        for uid, runtime in self.runtimes.items():
            ub = await session.get(Userbot, uid)
            if ub is not None:
                ub.last_heartbeat_at = _now()
                ub.current_worker_id = worker.id

    async def _set_status(self, userbot_id: int, status: str, *, error: str | None = None) -> None:
        async with async_session_factory() as session:
            try:
                ub = await session.get(Userbot, userbot_id)
                if ub is not None:
                    ub.status = status
                    if error is not None:
                        ub.error_message = error
                    if status == "RUNNING":
                        ub.last_heartbeat_at = _now()
                        self.retry_counts[userbot_id] = 0
                    await session.commit()
            except Exception as exc:  # noqa: BLE001
                await session.rollback()
                log.error("status update failed", extra_fields={"userbot_id": userbot_id, "error": str(exc)})

    async def _load_modules(self, session, user_id: int) -> tuple[list, dict]:
        stmt = (
            select(UserModule)
            .options(selectinload(UserModule.module), selectinload(UserModule.settings))
            .where(UserModule.user_id == user_id, UserModule.enabled.is_(True))
        )
        result = await session.execute(stmt)
        rows = list(result.scalars().all())
        module_classes = []
        module_settings: dict[str, dict] = {}
        for um in rows:
            cls = self.registry.get(um.module.key)
            if cls is not None:
                module_classes.append(cls)
                module_settings[cls.metadata.key] = {s.key: s.value for s in um.settings}
        return module_classes, module_settings
