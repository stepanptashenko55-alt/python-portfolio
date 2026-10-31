"""Telegram bot: AI answers from the FAQ, order collection and handoff to a human manager."""

import asyncio
import csv
import logging
import os
from datetime import datetime
from pathlib import Path

import anthropic
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from assistant import Assistant

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "conversations.csv"
ORDERS_FILE = BASE_DIR / "orders.csv"

router = Router()
assistant: Assistant  # created in main()


class Order(StatesGroup):
    product = State()
    quantity = State()
    address = State()
    phone = State()


def append_csv(path: Path, row: list) -> None:
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if new:
            header = ["time", "user_id", "username", "question", "answer"] if path == LOG_FILE else \
                     ["time", "user_id", "username", "product", "quantity", "address", "phone"]
            writer.writerow(header)
        writer.writerow([datetime.now().isoformat(timespec="seconds"), *row])


async def notify_admin(bot: Bot, text: str) -> None:
    admin_id = os.getenv("ADMIN_ID")
    if admin_id:
        await bot.send_message(admin_id, text)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    assistant.reset(message.from_user.id)
    await message.answer(
        f"Hi, {message.from_user.first_name}! I'm the assistant of {assistant.business}. "
        "Ask me anything, or type /order to place an order and /manager to talk to a human."
    )


@router.message(Command("manager"))
async def cmd_manager(message: Message, bot: Bot) -> None:
    await handoff(message, bot, message.text)


@router.message(Command("order"))
async def cmd_order(message: Message, state: FSMContext) -> None:
    await state.set_state(Order.product)
    await message.answer("What would you like to order?")


@router.message(Order.product)
async def order_product(message: Message, state: FSMContext) -> None:
    await state.update_data(product=message.text)
    await state.set_state(Order.quantity)
    await message.answer("How many?")


@router.message(Order.quantity)
async def order_quantity(message: Message, state: FSMContext) -> None:
    await state.update_data(quantity=message.text)
    await state.set_state(Order.address)
    await message.answer("Delivery address?")


@router.message(Order.address)
async def order_address(message: Message, state: FSMContext) -> None:
    await state.update_data(address=message.text)
    await state.set_state(Order.phone)
    await message.answer("And your phone number, please?")


@router.message(Order.phone)
async def order_phone(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.update_data(phone=message.text)
    await state.clear()
    user = message.from_user
    append_csv(ORDERS_FILE, [user.id, user.username, data["product"], data["quantity"], data["address"], data["phone"]])
    await message.answer("Thank you! Your order is received, a manager will confirm it shortly. 🙌")
    await notify_admin(bot, (
        f"🆕 <b>New order</b> from @{user.username or user.id}\n"
        f"Product: {data['product']}\nQuantity: {data['quantity']}\n"
        f"Address: {data['address']}\nPhone: {data['phone']}"
    ))


@router.message(F.text)
async def answer_question(message: Message, state: FSMContext, bot: Bot) -> None:
    await bot.send_chat_action(message.chat.id, "typing")
    try:
        reply = await assistant.ask(message.from_user.id, message.text)
    except anthropic.APIError:
        logging.exception("Claude API error")
        await handoff(message, bot, message.text)
        return

    append_csv(LOG_FILE, [message.from_user.id, message.from_user.username, message.text, reply.text])
    await message.answer(reply.text)
    if reply.handoff:
        await handoff(message, bot, message.text, reply_to_user=False)
    elif reply.order:
        await cmd_order(message, state)


async def handoff(message: Message, bot: Bot, question: str, reply_to_user: bool = True) -> None:
    user = message.from_user
    if reply_to_user:
        await message.answer("I've passed your message to a manager, they will reply here soon.")
    await notify_admin(bot, f"🙋 <b>Manager needed</b> for @{user.username or user.id} (id {user.id}):\n{question}")


def load_env(path: Path) -> None:
    """Minimal .env loader so the bot needs no extra dependencies."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


async def main() -> None:
    global assistant
    logging.basicConfig(level=logging.INFO)
    load_env(BASE_DIR / ".env")
    assistant = Assistant.from_file(BASE_DIR / os.getenv("FAQ_FILE", "faq.md"), business=os.getenv("BUSINESS_NAME", "our company"))
    bot = Bot(os.environ["BOT_TOKEN"], default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
