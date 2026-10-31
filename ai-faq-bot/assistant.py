"""AI assistant that answers customer questions strictly from the business FAQ using Claude."""

import os
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
HANDOFF = "[[HANDOFF]]"
ORDER = "[[ORDER]]"
MAX_HISTORY = 10  # messages kept per user (5 exchanges)

SYSTEM_TEMPLATE = """You are the customer assistant of {business}. You chat with customers in Telegram.

Answer ONLY using the FAQ below. Reply in the customer's language, briefly and politely, like a friendly human manager. Plain text, no markdown.

Rules:
- If the FAQ does not contain the answer, do not guess. Say you will pass the question to a manager and end your reply with {handoff}
- If the customer asks for a human, also end your reply with {handoff}
- If the customer wants to place an order or a booking, confirm briefly and end your reply with {order}

<faq>
{faq}
</faq>"""


@dataclass
class Reply:
    text: str
    handoff: bool = False
    order: bool = False


@dataclass
class Assistant:
    faq: str
    business: str = "our company"
    client: anthropic.AsyncAnthropic = field(default_factory=anthropic.AsyncAnthropic)
    history: dict[int, list[dict]] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path, business: str, **kwargs) -> "Assistant":
        return cls(faq=Path(path).read_text(encoding="utf-8"), business=business, **kwargs)

    @property
    def system(self) -> list[dict]:
        text = SYSTEM_TEMPLATE.format(business=self.business, faq=self.faq, handoff=HANDOFF, order=ORDER)
        # The FAQ is identical on every request, so cache it to cut cost and latency.
        return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

    async def ask(self, user_id: int, question: str) -> Reply:
        messages = self.history.setdefault(user_id, [])
        messages.append({"role": "user", "content": question})

        response = await self.client.beta.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=self.system,
            messages=messages,
            output_config={"effort": "low"},  # short FAQ answers do not need deep reasoning
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )

        if response.stop_reason == "refusal":
            messages.pop()
            return Reply("Let me pass your question to a manager.", handoff=True)

        raw = "".join(block.text for block in response.content if block.type == "text").strip()
        messages.append({"role": "assistant", "content": raw})
        del messages[:-MAX_HISTORY]
        return parse_reply(raw)

    def reset(self, user_id: int) -> None:
        self.history.pop(user_id, None)


def parse_reply(raw: str) -> Reply:
    return Reply(
        text=raw.replace(HANDOFF, "").replace(ORDER, "").strip(),
        handoff=HANDOFF in raw,
        order=ORDER in raw,
    )
