import asyncio
import logging
import aiohttp
import threading
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask, jsonify

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN", "8604347767:AAGNAm_cjMOi49OFOVHFqesEpuFLP_Db51E")
PORT = int(os.environ.get("PORT", 8080))
# ===============================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

conversation_history = {}

# ---------- Flask для health check ----------
flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return jsonify({"status": "ok", "bot_running": True})

def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()
# -------------------------------------------

async def get_ai_response(user_id: int, user_message: str) -> str:
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({"role": "user", "content": user_message})
    if len(conversation_history[user_id]) > 10:
        conversation_history[user_id] = conversation_history[user_id][-10:]

    url = "https://text.pollinations.ai/"
    payload = {
        "messages": conversation_history[user_id],
        "model": "openai"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as resp:
                if resp.status == 200:
                    reply_text = await resp.text()
                    reply_text = reply_text.strip()
                    if reply_text:
                        conversation_history[user_id].append({"role": "assistant", "content": reply_text})
                        return reply_text
                    else:
                        logging.warning("Pollinations AI вернул пустой ответ")
                        return "🤖 Нейросеть вернула пустой ответ. Попробуйте ещё раз."
                else:
                    error_text = await resp.text()
                    logging.error(f"Ошибка HTTP {resp.status}: {error_text}")
                    return f"❌ Ошибка сервера ИИ (код {resp.status}). Попробуйте позже."
    except asyncio.TimeoutError:
        logging.error("Таймаут при запросе к Pollinations AI")
        return "⏱️ Нейросеть не ответила вовремя. Попробуйте ещё раз."
    except Exception as e:
        logging.error(f"Исключение при запросе: {e}")
        return "⚠️ Произошла техническая ошибка. Пожалуйста, повторите позже."

@dp.business_message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот с искусственным интеллектом (через Pollinations AI).\n"
        "Просто напиши мне что-нибудь, и я отвечу.\n"
        "Команда /clear — очистить историю диалога."
    )

@dp.business_message(Command("clear"))
async def cmd_clear(message: types.Message):
    user_id = message.from_user.id
    if user_id in conversation_history:
        conversation_history[user_id] = []
        await message.answer("🧹 История нашего диалога очищена.")
    else:
        await message.answer("История диалога и так пуста.")

@dp.business_message()
async def answer_to_message(message: types.Message):
    if not message.text or message.text.isspace():
        await message.answer("Пожалуйста, напишите текстовое сообщение.")
        return

    await bot.send_chat_action(message.chat.id, action="typing")
    answer = await get_ai_response(message.from_user.id, message.text)
    await message.answer(answer + " (это ИИ бот)")

async def main():
    logging.info("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
