"""Payment settings and automation parse tests."""

from __future__ import annotations

from sqlalchemy import select

from app.database.models.settings import PaymentSetting


async def test_payment_setting_crud(db_session):
    ps = PaymentSetting(card_number="6037991234567890", card_owner="رضا فرهادی", is_active=True)
    db_session.add(ps)
    await db_session.flush()
    got = (await db_session.execute(select(PaymentSetting))).scalar_one()
    assert got.card_number == "6037991234567890"
    assert got.card_owner == "رضا فرهادی"


def test_parse_action_reply():
    from app.bot.bot import CentralBot

    t, p = CentralBot._parse_action("reply:سلام 👋")
    assert t == "reply"
    assert p == {"text": "سلام 👋"}


def test_parse_action_delete():
    from app.bot.bot import CentralBot

    t, p = CentralBot._parse_action("delete")
    assert t == "delete"
    assert p == {}


def test_parse_action_forward():
    from app.bot.bot import CentralBot

    t, p = CentralBot._parse_action("forward:-100123")
    assert t == "forward"
    assert p == {"to_chat": "-100123"}


def test_parse_action_invalid():
    from app.bot.bot import CentralBot

    t, p = CentralBot._parse_action("invalid")
    assert t is None
