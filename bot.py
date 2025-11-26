from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio
import aiohttp
from telegram.error import Conflict
import logging

# Включаем логирование
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
                'limit': 1
            }) as resp:
                data = await resp.json()
                if data.get('ok') and data.get('result'):
                    reactions = data.get('result', [])
                    if len(reactions) > 0:
                        print(f"[REACTION_DETECTED] Найдена реакция: {reactions[0]}")
                        return True
                return False
    except Exception as e:
        print(f"[DEBUG] Ошибка при проверке реакций: {e}")
        return False

async def check_reaction_and_timeout(msg_id, chat_id, timeout, bot):
    """Проверяет реакции во время таймера"""
    start_time = asyncio.get_event_loop().time()
    check_interval = 5
    
    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        
        has_reaction = await check_message_reactions(bot, chat_id, msg_id)
        
        if has_reaction:
            print(f"[✅ REACTION] Обнаружена реакция на сообщение ID {msg_id}!")
            if msg_id in pending_messages:
                pending_messages[msg_id]['has_reaction'] = True
            print(f"[✅ MARKED] Сообщение ID {msg_id} помечено - таймер отменён")
            return
        
        if elapsed >= timeout:
            if msg_id in pending_messages and not pending_messages[msg_id]['has_reaction']:
                try:
                    print(f"[❌ ACTION] Реакции не найдены. Пересылаю сообщение ID {msg_id}...")
                    await bot.forward_message(chat_id=DEST_CHAT_ID, from_chat_id=chat_id, message_id=msg_id)
                    await bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    pending_messages.pop(msg_id, None)
                    print(f"[✅ SUCCESS] Сообщение ID {msg_id} успешно переслано и удалено")
                except Exception as e:
                    print(f"[❌ ERROR] Ошибка: {e}")
            return
        
        if int(elapsed) % 30 == 0 and int(elapsed) > 0:
            remaining = timeout - int(elapsed)
            print(f"[⏱️  STATUS] Сообщение ID {msg_id}: {remaining} сек до пересылки")
        
        await asyncio.sleep(check_interval)

def main():
    """Основная функция"""
    app = Application.builder().token(API_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(SOURCE_CHAT_ID), handle_keyword_message))
    
    print("=" * 50)
    print("🤖 Бот запущен и готов к работе...")
    print(f"📍 Отслеживаемый канал/группа: {SOURCE_CHAT_ID}")
    print(f"🔑 Ключевое слово: {KEYWORD}")
    print(f"⏱️  Таймер: {TIMEOUT} секунд")
    print(f"➡️  Направление пересылки: {DEST_CHAT_ID}")
    print(f"👁️  Отслеживание реакций: ДА (проверка каждые 5 секунд)")
    print("=" * 50)
    
    try:
        app.run_polling(allowed_updates=["message"], drop_pending_updates=True)
    except Conflict as e:
        print(f"[ERROR] Конфликт: {e}")
        print("[INFO] Переподключаюсь через 5 секунд...")
        asyncio.sleep(5)
        main()

if __name__ == '__main__':
    main()
