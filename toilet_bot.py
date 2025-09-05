import os
import time
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Load token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram application
telegram_app = Application.builder().token(BOT_TOKEN).build()

# Your existing handlers (simplified example)
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚽 Toilet Bot is alive (Webhook mode)!")

telegram_app.add_handler(CommandHandler("start", start))

# Flask web app
flask_app = Flask(__name__)

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    """Receive updates from Telegram"""
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok", 200

@flask_app.route("/", methods=["GET"])
def home():
    return "Toilet Bot is running 🚀", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)
