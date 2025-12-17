from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, TypeHandler
import os
import asyncio
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

API_TOKEN = os.getenv('API_TOKEN', '8580700829:AAFLYKifYGoSE2rxQAcdfeuMYwyz1DLcyuk')
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
    
    pending_messages[msg_id] = {'has_reaction': False, 'chat_id': chat_id}
    
    print(f"[MESSAGE] Получено сообщение ID {msg_id} с ключевым словом '{KEYWORD}'")
    print(f"[TIMER] Начат таймер на {TIMEOUT} секунд...")
    
    asyncio.create_task(check_timeout(msg_id, chat_id, TIMEOUT, context.bot))

async def handle_message_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обновлений о реакциях"""
    if not update.message_reaction:
        return
    
    reaction = update.message_reaction
    msg_id = reaction.message_id
    chat_id = reaction.chat.id
    
    print(f"[🔔 REACTION_UPDATE] Получено обновление реакции:")
    print(f"    - Сообщение ID: {msg_id}")
    print(f"    - Чат ID: {chat_id}")
    print(f"    - Новые реакции: {reaction.new_reaction}")
    
    # Проверяем, есть ли новые реакции
    if reaction.new_reaction and len(reaction.new_reaction) > 0:
        print(f"[✅ REACTION_DETECTED] Реакция найдена на сообщение ID {msg_id}")
        if msg_id in pending_messages:
            pending_messages[msg_id]['has_reaction'] = True
            print(f"[✅ MARKED] Сообщение ID {msg_id} помечено как имеющее реакцию")

async def check_timeout(msg_id, chat_id, timeout, bot):
    """Проверяет таймер и пересылает сообщение если реакции нет"""
    start_time = asyncio.get_event_loop().time()
    
    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Если время истекло
        if elapsed >= timeout:
            print(f"[⏰ TIMEOUT] Время истекло для сообщения ID {msg_id}")
            if msg_id in pending_messages:
                if not pending_messages[msg_id]['has_reaction']:
                    try:
                        print(f"[❌ NO_REACTION] Реакции не найдены. Пересылаю сообщение ID {msg_id}...")
                        await bot.forward_message(chat_id=DEST_CHAT_ID, from_chat_id=chat_id, message_id=msg_id)
                        print(f"[🗑️  DELETING] Удаляю сообщение ID {msg_id}...")
                        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
                        pending_messages.pop(msg_id, None)
                        print(f"[✅ COMPLETED] Сообщение ID {msg_id} успешно переслано и удалено")
                    except Exception as e:
                        print(f"[❌ ERROR] Ошибка при пересылке: {e}")
                else:
                    print(f"[✅ REACTION_SAVED] Сообщение ID {msg_id} не пересылается (есть реакция)")
                    pending_messages.pop(msg_id, None)
            return
        
        # Выводим статус каждые 60 секунд
        if int(elapsed) % 60 == 0 and int(elapsed) > 0:
            remaining = timeout - int(elapsed)
            status = "✅ ЕСТЬ РЕАКЦИЯ" if pending_messages.get(msg_id, {}).get('has_reaction') else "❌ НЕТ РЕАКЦИИ"
            print(f"[⏱️  STATUS] Сообщение ID {msg_id}: {status}, осталось {remaining} сек")
        
        await asyncio.sleep(1)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    print(f"[❌ ERROR] Exception: {context.error}")

def main():
    """Основная функция"""
    app = Application.builder().token(API_TOKEN).build()
    
    # Обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(SOURCE_CHAT_ID), handle_keyword_message))
    
    # Обработчик реакций через TypeHandler
    app.add_handler(TypeHandler(Update, handle_message_reaction), group=1)
    
    app.add_error_handler(error_handler)
    
    print("=" * 60)
    print("🤖 Бот запущен и готов к работе...")
    print(f"📍 Отслеживаемый канал/группа: {SOURCE_CHAT_ID}")
    print(f"🔑 Ключевое слово: {KEYWORD}")
    print(f"⏱️  Таймер: {TIMEOUT} секунд")
    print(f"➡️  Направление пересылки: {DEST_CHAT_ID}")
    print(f"👁️  Отслеживание реакций: ДА (через message_reaction обновления)")
    print("=" * 60)
    
    app.run_polling(
        allowed_updates=["message", "message_reaction"],
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
