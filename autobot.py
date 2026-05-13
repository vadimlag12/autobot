import asyncio
import random
from telethon import TelegramClient, events
from telethon.tl.types import Message
from g4f.client import AsyncClient  # Используем асинхронную версию

# ================= НАСТРОЙКИ (ЗАПОЛНИТЕ ОБЯЗАТЕЛЬНО) =================
API_CONFIG = {
    'api_id': 123456,          # Ваш API ID (число) из my.telegram.org
    'api_hash': 'ВАШ_API_HASH_ЗДЕСЬ',  # Ваш API Hash (строка) из my.telegram.org
    'session_name': 'my_userbot_session'  # Название файла сессии (можно любое)
}

# Настройки нейросети g4f (не требует API-ключа!)
AI_CONFIG = {
    'model': 'gpt-3.5-turbo',   # Модель для использования
    # 'provider': None          # Можно оставить None или указать провайдера
}

RANDOM_DELAY = (1, 3)           # Случайная задержка перед ответом (секунды)
# ===================================================================

# Создаем клиента Telethon
client = TelegramClient(
    API_CONFIG['session_name'],
    API_CONFIG['api_id'],
    API_CONFIG['api_hash'],
    sequential_updates=True  # Обрабатываем сообщения по одному
)

# Создаем асинхронного клиента g4f для запросов к нейросети
ai_client = AsyncClient()


@client.on(events.NewMessage(incoming=True))
async def ai_auto_reply(event):
    # --- 1. Проверяем, что сообщение не от нас самих (чтобы не зациклиться) ---
    if event.out:
        return

    # --- 2. Можно добавить проверку на ботов ---
    # Если сообщение от бота, можно его пропустить, чтобы не отвечать на чужие автоответы
    # if event.sender_id and event.sender_id < 0:  # ID ботов обычно отрицательные
    #     return

    # --- 3. Получаем текст сообщения. Если он пустой (например, фото), пропускаем ---
    message_text = event.raw_text
    if not message_text or message_text.isspace():
        return

    # --- 4. Небольшая "человеческая" задержка перед ответом ---
    await asyncio.sleep(random.uniform(*RANDOM_DELAY))

    sender = await event.get_sender()
    sender_name = sender.first_name if sender else "Неизвестный пользователь"
    print(f"✉️  Получено сообщение от {sender_name}: {message_text[:50]}...")

    # --- 5. Запрашиваем ответ у нейросети ---
    try:
        response = await ai_client.chat.completions.create(
            model=AI_CONFIG['model'],
            messages=[
                {"role": "system", "content": "You are a helpful and friendly AI assistant, chatting on behalf of the user."},
                {"role": "user", "content": message_text}
            ],
            # provider=AI_CONFIG['provider']  # Раскомментируйте, если хотите указать провайдера
        )

        # Извлекаем текст ответа
        reply_text = response.choices[0].message.content.strip()
        if not reply_text:
            reply_text = "Извините, я не смог сформулировать ответ."

        # Отправляем ответ в тот же чат
        await event.reply(reply_text)
        print(f"🤖 Отправлен ответ: {reply_text[:50]}...")

    except Exception as e:
        # В случае любой ошибки (проблемы с сетью, g4f и т.д.) отправляем пользователю уведомление
        error_msg = "Извините, произошла ошибка при обращении к нейросети. Пожалуйста, попробуйте позже."
        await event.reply(error_msg)
        print(f"❌ Ошибка при запросе к g4f: {e}")


async def main():
    # Запускаем клиента
    await client.start()
    print("✅ Бот запущен и слушает все входящие сообщения.")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Бот остановлен пользователем.")
