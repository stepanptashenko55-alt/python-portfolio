import asyncio
from types import SimpleNamespace

import assistant as mod
from assistant import Assistant, parse_reply


class FakeMessages:
    def __init__(self, text: str, stop_reason: str = "end_turn"):
        self.text, self.stop_reason, self.calls = text, stop_reason, []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=self.text)],
        )


def make(text: str, stop_reason: str = "end_turn") -> tuple[Assistant, FakeMessages]:
    messages = FakeMessages(text, stop_reason)
    client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    return Assistant(faq="Open 8:00-21:00.", business="Test Cafe", client=client), messages


def test_parse_reply_markers():
    assert parse_reply("Sure, let's do it! [[ORDER]]") == mod.Reply("Sure, let's do it!", order=True)
    assert parse_reply("I'll ask a manager. [[HANDOFF]]").handoff
    assert parse_reply("We open at 8:00.") == mod.Reply("We open at 8:00.")


def test_ask_sends_faq_and_keeps_history():
    bot, messages = make("We are open from 8:00 to 21:00.")
    reply = asyncio.run(bot.ask(1, "When are you open?"))

    assert reply.text == "We are open from 8:00 to 21:00."
    call = messages.calls[0]
    assert call["model"] == mod.MODEL
    assert "Open 8:00-21:00." in call["system"][0]["text"]
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert call["fallbacks"] == "default"
    assert [m["role"] for m in bot.history[1]] == ["user", "assistant"]


def test_history_is_trimmed():
    bot, _ = make("ok")
    for i in range(20):
        asyncio.run(bot.ask(7, f"question {i}"))
    assert len(bot.history[7]) == mod.MAX_HISTORY
    assert bot.history[7][0]["role"] == "user"


def test_refusal_hands_off_without_polluting_history():
    bot, _ = make("", stop_reason="refusal")
    reply = asyncio.run(bot.ask(3, "something"))
    assert reply.handoff
    assert bot.history[3] == []
