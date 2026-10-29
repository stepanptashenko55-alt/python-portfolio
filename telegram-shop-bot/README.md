# Telegram Shop Bot

A ready-to-use Telegram bot for a small online shop, built with Python and aiogram 3.

## Features
- Product catalog with inline buttons (products are edited in `products.json`, no coding needed)
- Shopping cart: add items, view total, clear cart
- Checkout flow: collects customer name and phone number
- Instant order notification to the shop owner in Telegram
- `/orders` admin command: last 10 orders
- Orders stored in a local SQLite database

## Quick start
1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Find your Telegram user ID (for example with [@userinfobot](https://t.me/userinfobot)).
3. Install and run:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env   # then put your token and admin ID into .env
   python bot.py
   ```

## Customization ideas
Payments (Stripe / Telegram Payments), product photos, categories, Google Sheets order export,
multi-language interface, admin panel for editing products.
