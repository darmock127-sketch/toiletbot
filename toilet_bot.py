# toilet_bot.py
# pip install python-telegram-bot==20.7
import os, json, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

STATE_FILE = "toilet_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f: return json.load(f)
    return {"occupied_by": None, "since": 0, "queue": [], "pinned_msg_id": None}

def save_state(s):
    with open(STATE_FILE, "w") as f: json.dump(s, f)

def status_text(s):
    occ = s["occupied_by"]; q = s["queue"]
    if occ:
        mins = int((time.time() - s["since"]) // 60)
        return f"🚫 Occupied by {occ} ({mins} min)\nQueue: " + (", ".join(q) if q else "—")
    return "✅ FREE\nQueue: " + (", ".join(q) if q else "—")

def kb(occupied):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("I’m out ✅", callback_data="out")]] if occupied
        else [[InlineKeyboardButton("I’m in 🚽", callback_data="in")]]
    )

async def ensure_pin(chat_id, ctx: ContextTypes.DEFAULT_TYPE, s):
    if s.get("pinned_msg_id"): return
    m = await ctx.bot.send_message(chat_id, "✅ FREE\nQueue: —")
    try: await ctx.bot.pin_chat_message(chat_id, m.message_id)
    except: pass
    s["pinned_msg_id"] = m.message_id; save_state(s)

async def refresh_pin(chat_id, ctx, s):
    if not s.get("pinned_msg_id"): return
    try:
        await ctx.bot.edit_message_text(
            status_text(s), chat_id, s["pinned_msg_id"], reply_markup=kb(bool(s["occupied_by"]))
        )
    except: pass

async def cmd_in(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = load_state(); await ensure_pin(update.effective_chat.id, ctx, s)
    user = f"@{update.effective_user.username}" if update.effective_user.username else update.effective_user.full_name
    if s["occupied_by"] is None:
        s["occupied_by"] = user; s["since"] = time.time()
        save_state(s); await update.message.reply_text(f"✅ You’re in, {user}.")
    else:
        if user != s["occupied_by"] and user not in s["queue"]:
            s["queue"].append(user); save_state(s)
            await update.message.reply_text(f"Queued ⏳ position #{len(s['queue'])}, {user}.")
    await refresh_pin(update.effective_chat.id, ctx, s)

async def cmd_out(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = load_state(); await ensure_pin(update.effective_chat.id, ctx, s)
    if s["occupied_by"] is None:
        await update.message.reply_text("It’s already free."); return
    s["occupied_by"] = None; s["since"] = 0
    nxt = s["queue"].pop(0) if s["queue"] else None
    if nxt:
        s["occupied_by"] = nxt; s["since"] = time.time()
        await update.message.reply_text(f"Next up: {nxt} 🚽")
    else:
        await update.message.reply_text("Toilet is now FREE ✅")
    save_state(s); await refresh_pin(update.effective_chat.id, ctx, s)

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = load_state()
    await ensure_pin(update.effective_chat.id, ctx, s)
    await update.message.reply_text(status_text(s))

async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    # Route to /in or /out based on button
    if q.data == "in":
        update.effective_user = q.from_user
        update.effective_chat = q.message.chat
        class Msg:  # mock object so cmd_in can send a reply
            async def reply_text(self, t): await ctx.bot.send_message(q.message.chat_id, t)
        update.message = Msg()
        await cmd_in(update, ctx)
    elif q.data == "out":
        update.effective_user = q.from_user
        update.effective_chat = q.message.chat
        class Msg:
            async def reply_text(self, t): await ctx.bot.send_message(q.message.chat_id, t)
        update.message = Msg()
        await cmd_out(update, ctx)

def main():
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN env var not set. export BOT_TOKEN=\"...\"")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("in", cmd_in))
    app.add_handler(CommandHandler("out", cmd_out))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CallbackQueryHandler(on_button))
    app.run_polling()

if __name__ == "__main__":
    main()
