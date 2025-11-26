from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, ChatMemberHandler
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
    
    pending_messages[msg_id] = {'has_reaction': False}
    
    print(f"[MESSAGE] Получено сообщение ID {msg_id} с ключевым словом '{KEYWORD}'")
    print(f"[TIMER] Начат таймер на {TIMEOUT} секунд...")
    
    # Запускаем таймер в отдельной задаче
    asyncio.create_task(check_timeout(msg_id, chat_id, context.bot))

async def check_timeout(msg_id, chat_id, bot):
    """Проверка таймера и пересылка сообщения"""
    await asyncio.sleep(TIMEOUT)
    
    if msg_id in pending_messages and not pending_messages[msg_id]['has_reaction']:
        try:
            print(f"[ACTION] Реакции не найдены. Пересылаю сообщение ID {msg_id}...")
            await bot.forward_message(chat_id=DEST_CHAT_ID, from_chat_id=chat_id, message_id=msg_id)
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            pending_messages.pop(msg_id, None)
            print(f"[SUCCESS] Сообщение ID {msg_id} успешно переслано и удалено")
        except Exception as e:
            print(f"[ERROR] Ошибка при обработке сообщения {msg_id}: {e}")

async def handle_message_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик реакций на сообщения"""
    print(f"[DEBUG] Обновление получено: {update.update_id}")
    
    if not update.message_reaction:
        return
    
    reaction = update.message_reaction
    msg_id = reaction.message_id
    chat_id = reaction.chat.id
    
    print(f"[DEBUG] Получена реакция на сообщение {msg_id} в чате {chat_id}")
    print(f"[DEBUG] new_reaction: {reaction.new_reaction}")
    
    if chat_id == SOURCE_CHAT_ID and msg_id in pending_messages:
        if reaction.new_reaction:
            print(f"[REACTION] Обнаружена реакция на сообщение ID {msg_id}")
            pending_messages[msg_id]['has_reaction'] = True
            print(f"[MARKED] Сообщение ID {msg_id} помечено как имеющее реакцию - таймер отменён")

async def main():
    """Основная функция"""
    app = Application.builder().token(API_TOKEN).build()
    
    # Добавляем обработчики
    # Обработчик текстовых сообщений с ключевым словом
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(SOURCE_CHAT_ID), handle_keyword_message))
    
    # Обработчик реакций (через специальный обработчик, а не через MessageHandler)
    # Мы добавляем его вручную в process_update
    
    print("🤖 Бот запущен и готов к работе...")
    print(f"📍 Отслеживаемый канал/группа: {SOURCE_CHAT_ID}")
    print(f"🔑 Ключевое слово: {KEYWORD}")
    print(f"⏱️  Таймер: {TIMEOUT} секунд")
    print(f"➡️  Направление пересылки: {DEST_CHAT_ID}")
    print("-" * 50)
    
    # Переопределяем process_update для обработки реакций
    original_process_update = app.process_update
    
    async def process_update_with_reactions(update):
        # Обрабатываем реакции
        if update.message_reaction:
            await handle_message_reaction(update, ContextTypes.DEFAULT_TYPE())
        # Обрабатываем остальное
        return await original_process_update(update)
    
    app.process_update = process_update_with_reactions
    
    # Разрешить получение message_reaction обновлений
    await app.run_polling(allowed_updates=["message", "message_reaction"])

if __name__ == '__main__':
    asyncio.run(main())
