# AI FAQ Assistant for Telegram

A Telegram bot that answers customers 24/7 like a friendly manager, using **only your own FAQ document**,
built with Python, aiogram 3 and Claude (Anthropic API).

## What it does
- Answers questions in natural language from `faq.md` (opening hours, prices, delivery, returns...), in the customer's language
- Never invents answers: if the FAQ has no answer, it says so and **hands the conversation to a human manager**
- Recognises when a customer wants to order or book and starts a short order form (product, quantity, address, phone)
- Sends new orders and handoff requests to the owner in Telegram instantly
- Logs every conversation and order to CSV files (easy to open in Excel or import into Google Sheets)
- Remembers the last few messages, so follow-up questions work ("and on Sunday?")
- The FAQ is cached between requests, which keeps answers fast and cheap

## Quick start
1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Get an API key at [console.anthropic.com](https://console.anthropic.com).
3. Edit `faq.md` with your own business information (plain text, no coding).
4. Install and run:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env   # put your tokens into .env
   python bot.py
   ```

## Commands
| Command | Action |
|---|---|
| `/start` | Greeting, resets the conversation |
| `/order` | Order or booking form |
| `/manager` | Ask for a human manager |

## Tests
```bash
pytest
```

## Customization ideas
Google Sheets instead of CSV, CRM integration, payments, WhatsApp or website chat widget,
answers from PDFs or a large knowledge base, admin panel for editing the FAQ.
