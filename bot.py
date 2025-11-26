import telebot
import threading
import time
import os

API_TOKEN = os.getenv('API_TOKEN', '8188816335:AAHnLxlKDfTvcH_ILzTZT81kTj9CRIpgEZo')
SOURCE_CHAT_ID = int(os.getenv('SOURCE_CHAT_ID', '2228201497'))
DEST_CHAT_ID = int(os.getenv('DEST_CHAT_ID', '2194287037'))
KEYWORD = os.getenv('KEYWORD', '$$$')
TIMEOUT = int(os.getenv('TIMEOUT', '3600'))

bot = telebot.TeleBot(API_TOKEN)
pending_messages = {}

@bot.message_handler(func=lambda message: message.chat.id == SOURCE_CHAT_ID and message.text and message.text.startswith(KEYWORD))
def handle_keyword_message(message):
    msg_id = message.message_id
    chat_id = message.chat.id
    pending_messages[msg_id] = {'has_reaction': False, 'timer_started': True}
    
    print(f"[MESSAGE] Получено сообщение ID {msg_id} с ключевым словом '{KEYWORD}'")
    print(f"[TIMER] Начат таймер на {TIMEOUT} секунд...")
    
    def check_timeout():
        time.sleep(TIMEOUT)
        if msg_id in pending_messages and not pending_messages[msg_id]['has_reaction']:
            try:
                print(f"[ACTION] Реакции не найдены. Пересылаю сообщение ID {msg_id}...")
                bot.forward_message(DEST_CHAT_ID, chat_id, msg_id)
                bot.delete_message(chat_id, msg_id)
                pending_messages.pop(msg_id, None)
                print(f"[SUCCESS] Сообщение ID {msg_id} успешно переслано и удалено")
            except Exception as e:
                print(f"[ERROR] Ошибка при обработке сообщения {msg_id}: {e}")
    
    thread = threading.Thread(target=check_timeout, daemon=True)
    thread.start()

@bot.message_reaction_handler()
def handle_reaction(reaction: telebot.types.MessageReactionUpdated):
    """Обработчик реакций на сообщения"""
    msg_id = reaction.message_id
    chat_id = reaction.chat.id
    
    # Проверяем, это реакция в нашем канале и на наше отслеживаемое сообщение
    if chat_id == SOURCE_CHAT_ID and msg_id in pending_messages:
        if reaction.new_reaction:  # Если реакция добавлена
            print(f"[REACTION] Обнаружена реакция на сообщение ID {msg_id}")
            pending_messages[msg_id]['has_reaction'] = True
            print(f"[MARKED] Сообщение ID {msg_id} помечено как имеющее реакцию - таймер отменён")

if __name__ == '__main__':
    print("🤖 Бот запущен и готов к работе...")
    print(f"📍 Отслеживаемый канал/группа: {SOURCE_CHAT_ID}")
    print(f"🔑 Ключевое слово: {KEYWORD}")
    print(f"⏱️  Таймер: {TIMEOUT} секунд")
    print(f"➡️  Направление пересылки: {DEST_CHAT_ID}")
    print("-" * 50)
    
    bot.infinity_polling()
