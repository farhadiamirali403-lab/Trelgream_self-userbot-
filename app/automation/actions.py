"""Action execution for the automation engine."""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

log = get_logger("automation.actions")


async def execute_action(client, event, action_type: str, payload: dict | None) -> None:
    """Execute a single action using the userbot client and event."""
    payload = payload or {}
    try:
        if action_type == "reply":
            text = payload.get("text", "")
            await event.reply(text)
        elif action_type == "delete":
            await event.delete()
        elif action_type == "forward":
            to_chat = payload.get("to_chat")
            if to_chat:
                await client.forward_messages(to_chat, event.message)
        elif action_type == "send":
            chat = payload.get("chat")
            text = payload.get("text", "")
            if chat:
                await client.send_message(chat, text)
        elif action_type == "mute":
            if payload.get("user_id"):
                from telethon.tl.functions.channels import EditBannedRequest
                from telethon.tl.types import ChatBannedRights

                await client(
                    EditBannedRequest(
                        event.chat_id,
                        payload["user_id"],
                        ChatBannedRights(until_date=None, send_messages=True),
                    )
                )
        else:
            log.warning("unknown action type", extra_fields={"action_type": action_type})
    except Exception as exc:  # noqa: BLE001
        log.error("action execution failed", extra_fields={"action_type": action_type, "error": str(exc)})


async def execute_actions(client, event, actions: list) -> None:
    for action in actions:
        await execute_action(client, event, action.action_type, action.payload)
