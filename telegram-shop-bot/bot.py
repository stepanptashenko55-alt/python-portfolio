"""Telegram shop bot: catalog, cart, checkout and order notifications for the admin."""

import asyncio
import json
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import db

BASE_DIR = Path(__file__).parent
PRODUCTS = {p["id"]: p for p in json.loads((BASE_DIR / "products.json").read_text(encoding="utf-8"))}

router = Router()


class Checkout(StatesGroup):
    name = State()
    phone = State()


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Catalog", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 My cart", callback_data="cart")],
    ])


def catalog_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{p['name']} — ${p['price']:.2f}", callback_data=f"product:{pid}")]
        for pid, p in PRODUCTS.items()
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Back", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def format_cart(user_id: int) -> tuple[str, float]:
    items = db.get_cart(user_id)
    if not items:
        return "Your cart is empty.", 0.0
    lines, total = [], 0.0
    for product_id, qty in items:
        product = PRODUCTS[product_id]
        subtotal = product["price"] * qty
        total += subtotal
        lines.append(f"• {product['name']} × {qty} = ${subtotal:.2f}")
    lines.append(f"\n<b>Total: ${total:.2f}</b>")
    return "\n".join(lines), total


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        f"Hi, {message.from_user.first_name}! 👋\nWelcome to our shop. What would you like to do?",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "menu")
async def show_menu(call: CallbackQuery) -> None:
    await call.message.edit_text("Main menu:", reply_markup=main_menu())


@router.callback_query(F.data == "catalog")
async def show_catalog(call: CallbackQuery) -> None:
    await call.message.edit_text("Choose a product:", reply_markup=catalog_menu())


@router.callback_query(F.data.startswith("product:"))
async def show_product(call: CallbackQuery) -> None:
    pid = call.data.split(":", 1)[1]
    product = PRODUCTS[pid]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add to cart", callback_data=f"add:{pid}")],
        [InlineKeyboardButton(text="⬅️ Catalog", callback_data="catalog")],
    ])
    await call.message.edit_text(
        f"<b>{product['name']}</b>\n{product['description']}\n\nPrice: ${product['price']:.2f}",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(call: CallbackQuery) -> None:
    pid = call.data.split(":", 1)[1]
    db.add_to_cart(call.from_user.id, pid)
    await call.answer(f"{PRODUCTS[pid]['name']} added to cart ✅")


@router.callback_query(F.data == "cart")
async def show_cart(call: CallbackQuery) -> None:
    text, total = format_cart(call.from_user.id)
    rows = []
    if total:
        rows.append([InlineKeyboardButton(text="✅ Checkout", callback_data="checkout")])
        rows.append([InlineKeyboardButton(text="🗑 Clear cart", callback_data="clear")])
    rows.append([InlineKeyboardButton(text="⬅️ Back", callback_data="menu")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data == "clear")
async def clear_cart(call: CallbackQuery) -> None:
    db.clear_cart(call.from_user.id)
    await call.message.edit_text("Cart cleared.", reply_markup=main_menu())


@router.callback_query(F.data == "checkout")
async def start_checkout(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Checkout.name)
    await call.message.answer("Please enter your name:")
    await call.answer()


@router.message(Checkout.name)
async def checkout_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(Checkout.phone)
    await message.answer("Now enter your phone number:")


@router.message(Checkout.phone)
async def checkout_phone(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    user_id = message.from_user.id
    cart_text, total = format_cart(user_id)
    order_id = db.create_order(user_id, data["name"], message.text.strip(), total)
    db.clear_cart(user_id)

    await message.answer(f"Thank you! Order #{order_id} is placed. We will contact you soon. 🙌",
                         reply_markup=main_menu())
    admin_id = os.getenv("ADMIN_ID")
    if admin_id:
        await bot.send_message(
            admin_id,
            f"🆕 <b>New order #{order_id}</b>\nName: {data['name']}\nPhone: {message.text.strip()}\n"
            f"User: @{message.from_user.username or user_id}\n\n{cart_text}",
        )


@router.message(Command("orders"))
async def cmd_orders(message: Message) -> None:
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        return
    orders = db.list_orders(limit=10)
    if not orders:
        await message.answer("No orders yet.")
        return
    lines = [f"#{o[0]} | {o[1]} | {o[2]} | ${o[3]:.2f} | {o[4]}" for o in orders]
    await message.answer("<b>Last orders:</b>\n" + "\n".join(lines))


def load_env(path: Path) -> None:
    """Minimal .env loader so the bot has no extra dependencies."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    load_env(BASE_DIR / ".env")
    db.init()
    bot = Bot(os.environ["BOT_TOKEN"], default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
