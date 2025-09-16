import os
import asyncio
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from database import init_db, add_bot, get_bots, update_greeting
from bot_instance import BotInstance

# === Logging (important for debugging on Render) ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# === Load admin config ===
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

if not ADMIN_BOT_TOKEN:
    raise ValueError("❌ Missing ADMIN_BOT_TOKEN! Set it in Render environment.")

# === Flask app (keeps Render alive) ===
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Manager Running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# === Worker bots container ===
worker_apps = []

async def check_admin(update: Update):
    return update.effective_user.id == ADMIN_USER_ID

# === Manager Bot Commands ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        await update.message.reply_text("⛔ You are not allowed.")
        return
    await update.message.reply_text(
        "✅ Manager bot ready.\n\n"
        "Commands:\n"
        "/addbot <token> <greeting>\n"
        "/listbots\n"
        "/setgreeting <id> <text>\n"
        "/broadcast <msg>"
    )

async def addbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /addbot <token> [greeting]")
        return
    token = context.args[0]
    greeting = " ".join(context.args[1:]) if len(context.args) > 1 else "Hello!"
    add_bot(token, greeting)
    await update.message.reply_text("🤖 Bot added. Restarting worker...")
    await restart_workers(update)

async def listbots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    bots = get_bots()
    msg = "\n".join([f"ID: {b[0]} | Greeting: {b[2]}" for b in bots])
    await update.message.reply_text(msg or "No bots added yet.")

async def setgreeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setgreeting <id> <text>")
        return
    bot_id = int(context.args[0])
    greeting = " ".join(context.args[1:])
    update_greeting(bot_id, greeting)
    await update.message.reply_text(f"✅ Greeting updated for bot {bot_id}")
    await restart_workers(update)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    msg = " ".join(context.args)
    bots = get_bots()
    for _, token, _ in bots:
        app = Application.builder().token(token).build()
        try:
            await app.bot.send_message(chat_id=ADMIN_USER_ID, text=f"[Broadcast] {msg}")
        except Exception as e:
            logger.error(f"Broadcast failed for bot {token[:10]}...: {e}")
    await update.message.reply_text("📢 Broadcast sent.")

# === Restart worker bots ===
async def restart_workers(update=None):
    global worker_apps
    for app in worker_apps:
        try:
            await app.shutdown()
        except Exception:
            pass
    worker_apps.clear()

    for _, token, greeting in get_bots():
        bot = BotInstance(token, greeting)
        worker_apps.append(bot.start())

    # Start them in background
    asyncio.create_task(asyncio.gather(*(b.run_polling() for b in worker_apps)))

# === Main entrypoint ===
async def main():
    init_db()

    # Manager bot
    app_manager = Application.builder().token(ADMIN_BOT_TOKEN).build()
    app_manager.add_handler(CommandHandler("start", start))
    app_manager.add_handler(CommandHandler("addbot", addbot))
    app_manager.add_handler(CommandHandler("listbots", listbots))
    app_manager.add_handler(CommandHandler("setgreeting", setgreeting))
    app_manager.add_handler(CommandHandler("broadcast", broadcast))

    await restart_workers()
    logger.info("✅ Manager bot started and workers initialized.")
    await app_manager.run_polling()

if __name__ == "__main__":
    # Run Flask in background
    threading.Thread(target=run_flask, daemon=True).start()

    # Run manager bot + workers
    asyncio.run(main())
