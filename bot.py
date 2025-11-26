from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio
import aiohttp
from telegram.error import Conflict
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
    
    pending_messages[msg_id] = {'has_reaction': False, 'chat_id': chat_id}
    
    print(f"[MESSAGE] Получено сообщение ID {msg_id} с ключевым словом '{KEYWORD}'")
    print(f"[TIMER] Начат таймер на {TIMEOUT} секунд...")
    
    asyncio.create_task(check_reaction_and_timeout(msg_id, chat_id, TIMEOUT, context.bot))

async def check_message_reactions(bot, chat_id, msg_id):
    """Проверяет наличие реакций на сообщение через Telegram API"""
    try:
        url = f"https://api.telegram.org/bot{API_TOKEN}/getMessageReactionsList"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                'chat_id': chat_id,
                'message_id': msg_id,
                'limit': 100
            }, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if data.get('ok'):
                    result = data.get('result', [])
                    if result and len(result) > 0:
                        print(f"[✅ REACTION_FOUND] Найдены реакции: {[r.get('type') for r in result]}")
                        return True
                else:
                    print(f"[ERROR] API error: {data.get('description')}")
                return False
    except Exception as e:
        print(f"[DEBUG] Ошибка при проверке реакций: {e}")
        return False

async def check_reaction_and_timeout(msg_id, chat_id, timeout, bot):
    """Проверяет реакции во время таймера"""
    start_time = asyncio.get_event_loop().time()
    check_interval = 3  # Проверяем каждые 3 секунды для большей чувствительности
    
    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Проверяем реакции
        print(f"[🔍 CHECK] Проверяю реакции на сообщение {msg_id}... (прошло {int(elapsed)} сек)")
        has_reaction = await check_message_reactions(bot, chat_id, msg_id)
        
        if has_reaction:
            print(f"[✅ SUCCESS_REACTION] Обнаружена реакция на сообщение ID {msg_id}!")
            if msg_id in pending_messages:
                pending_messages[msg_id]['has_reaction'] = True
            print(f"[✅ CANCELLED] Таймер отменён для сообщения ID {msg_id}")
            return
        
        # Если время истекло
        if elapsed >= timeout:
            print(f"[⏰ TIMEOUT] Время истекло для сообщения ID {msg_id}")
            if msg_id in pending_messages and not pending_messages[msg_id]['has_reaction']:
                try:
                    print(f"[➡️  FORWARDING] Пересылаю сообщение ID {msg_id}...")
                    await bot.forward_message(chat_id=DEST_CHAT_ID, from_chat_id=chat_id, message_id=msg_id)
                    print(f"[🗑️  DELETING] Удаляю сообщение ID {msg_id}...")
                    await bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    pending_messages.pop(msg_id, None)
                    print(f"[✅ COMPLETED] Сообщение ID {msg_id} успешно переслано и удалено")
                except Exception as e:
                    print(f"[❌ ERROR] Ошибка при пересылке: {e}")
            return
        
        # Выводим статус каждые 60 секунд
        if int(elapsed) % 60 == 0 and int(elapsed) > 0:
            remaining = timeout - int(elapsed)
            print(f"[⏱️  STATUS] Сообщение ID {msg_id}: осталось {remaining} сек")
        
        await asyncio.sleep(check_interval)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    print(f"[❌ ERROR] Exception while handling an update: {context.error}")

def main():
    """Основная функция"""
    app = Application.builder().token(API_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(SOURCE_CHAT_ID), handle_keyword_message))
    app.add_error_handler(error_handler)
    
    print("=" * 60)
    print("🤖 Бот запущен и готов к работе...")
    print(f"📍 Отслеживаемый канал/группа: {SOURCE_CHAT_ID}")
    print(f"🔑 Ключевое слово: {KEYWORD}")
    print(f"⏱️  Таймер: {TIMEOUT} секунд")
    print(f"➡️  Направление пересылки: {DEST_CHAT_ID}")
    print(f"👁️  Отслеживание реакций: ДА (проверка каждые 3 секунды)")
    print("=" * 60)
    
    app.run_polling(
        allowed_updates=["message", "message_reaction"],
        drop_pending_updates=True,
        poll_interval=0.5
    )

if __name__ == '__main__':
    main()
