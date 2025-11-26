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

@bot.message_handler(func=lambda message: message.chat.id == SOURCE_CHAT_ID and message.text.startswith(KEYWORD))
def handle_keyword_message(message):
    msg_id = message.message_id
    chat_id = message.chat.id
    pending_messages[msg_id] = False
    
    def check_timeout():
        time.sleep(TIMEOUT)
        if not pending_messages.get(msg_id):
            try:
                bot.forward_message(DEST_CHAT_ID, chat_id, msg_id)
                bot.delete_message(chat_id, msg_id)
                pending_messages.pop(msg_id, None)
            except Exception as e:
                print(f"Ошибка: {e}")
    
    thread = threading.Thread(target=check_timeout, daemon=True)
    thread.start()

if __name__ == '__main__':
    print("Bot started...")
    bot.infinity_polling()
