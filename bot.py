from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio

API_TOKEN = os.getenv('API_TOKEN', '8188816335:AAHnLxlKDfTvcH_ILzTZT81kTj9CRIpgEZo')
SOURCE_CHAT_ID = int(os.getenv('SOURCE_CHAT_ID', '2228201497'))
DEST_CHAT_ID = int(os.getenv('DEST_CHAT_ID', '2194287037'))
KEYWORD = os.getenv('KEYWORD', '$$$')
TIMEOUT = int(os.getenv('TIMEOUT', '3600'))

pending_messages = {}

async def handle_keyword_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений с ключевым словом"""
    if not update.message or not update.message.text:
        return
    
    msg_id = update.message.message_id
    chat_id = update.message.chat.id
    
    if not update.message.text.startswith(KEYWORD):
        return
    
    pending_messages[msg_id] = True
    
    print(f"[MESSAGE] Получено сообщение ID {msg_id} с ключевым словом '{KEYWORD}'")
    print(f"[TIMER] Начат таймер на {TIMEOUT} секунд...")
    
    # Запускаем таймер в отдельной задаче
    asyncio.create_task(check_timeout(msg_id, chat_id, context.bot))

async def check_timeout(msg_id, chat_id, bot):
    """Проверка таймера и пересылка сообщения"""
    await asyncio.sleep(TIMEOUT)
    
    if msg_id in pending_messages:
        try:
            print(f"[ACTION] Пересылаю сообщение ID {msg_id}...")
            await bot.forward_message(chat_id=DEST_CHAT_ID, from_chat_id=chat_id, message_id=msg_id)
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            pending_messages.pop(msg_id, None)
            print(f"[SUCCESS] Сообщение ID {msg_id} успешно переслано и удалено")
        except Exception as e:
            print(f"[ERROR] Ошибка: {e}")

async def main():
    """Основная функция"""
    app = Application.builder().token(API_TOKEN).build()
    
    # Обработчик текстовых сообщений с ключевым словом
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(SOURCE_CHAT_ID), handle_keyword_message))
    
    print("🤖 Бот запущен и готов к работе...")
    print(f"📍 Отслеживаемый канал/группа: {SOURCE_CHAT_ID}")
    print(f"🔑 Ключевое слово: {KEYWORD}")
    print(f"⏱️  Таймер: {TIMEOUT} секунд")
    print(f"➡️  Направление пересылки: {DEST_CHAT_ID}")
    print("-" * 50)
    
    await app.run_polling(allowed_updates=["message"])

if __name__ == '__main__':
    asyncio.run(main())
