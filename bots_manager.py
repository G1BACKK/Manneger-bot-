import os
import json
import asyncio
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Flask app (keeps Render service alive)
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Bot Manager is running!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# ====================
# BOT MANAGER SECTION
# ====================

# Get manager bot token
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
if not ADMIN_BOT_TOKEN:
    raise ValueError("❌ Missing ADMIN_BOT_TOKEN env var in Render!")

# Simple JSON storage for worker bots
DB_FILE = "bots_db.json"

def load_bots():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_bots(bots):
    with open(DB_FILE, "w") as f:
        json.dump(bots, f, indent=2)

worker_bots = load_bots()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Manager bot ready.\n"
        "Commands:\n"
        "/addbot <token> <greeting>\n"
        "/listbots\n"
        "/broadcast <message>"
    )

async def addbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addbot <token> <greeting>")
        return

    token = context.args[0]
    greeting = " ".join(context.args[1:])
    worker_bots[token] = {"greeting": greeting}
    save_bots(worker_bots)
    await update.message.reply_text("✅ Worker bot added successfully.")

async def listbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not worker_bots:
        await update.message.reply_text("No worker bots added yet.")
        return
    msg = "🤖 Worker Bots:\n"
    for i, (token, cfg) in enumerate(worker_bots.items(), start=1):
        msg += f"{i}. Greeting: {cfg['greeting']}\n"
    await update.message.reply_text(msg)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    # (Demo: just confirms; you’d loop over worker bots and send here)
    await update.message.reply_text(f"📢 Broadcast to all: {message}")

async def main():
    logger.info("🚀 Starting Manager Bot...")

    app = ApplicationBuilder().token(ADMIN_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addbot", addbot))
    app.add_handler(CommandHandler("listbots", listbots))
    app.add_handler(CommandHandler("broadcast", broadcast))

    logger.info("✅ Manager bot initialized. Waiting for commands...")
    await app.run_polling()

if __name__ == "__main__":
    logger.info("🚀 Launching Flask + Manager...")
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
