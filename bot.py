from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import asyncio
import os

API_TOKEN = os.getenv('API_TOKEN', '8188816335:AAHnLxlKDfTvcH_ILzTZT81kTj9CRIpgEZo')
SOURCE_CHAT_ID = int(os.getenv('SOURCE_CHAT_ID', '2228201497'))
DEST_CHAT_ID = int(os.getenv('DEST_CHAT_ID', '2194287037'))
KEYWORD = os.getenv('KEYWORD', '$$$')
TIMEOUT = int(os.getenv('TIMEOUT', '3600'))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
pending_messages = {}

@dp.message_handler(lambda message: message.chat.id == SOURCE_CHAT_ID and message.text and message.text.startswith(KEYWORD))
async def keyword_message(message: types.Message):
    msg_id = message.message_id
    chat_id = message.chat.id
    pending_messages[msg_id] = False

    await asyncio.sleep(TIMEOUT)
    if not pending_messages.get(msg_id):  # Нет реакции
        await bot.forward_message(DEST_CHAT_ID, chat_id, msg_id)
        await bot.delete_message(chat_id, msg_id)
        pending_messages.pop(msg_id, None)

@dp.edited_message_handler()
@dp.message_handler()
async def reaction_handler(message: types.Message):
    # Здесь обработка реакции — если реализовать через Bot API >= 6.0 и доступные данные о реакциях
    reactions = getattr(message, "reactions", None)
    if reactions:
        if pending_messages.get(message.message_id) is not None:
            pending_messages[message.message_id] = True

if __name__ == '__main__':
    executor.start_polling(dp)
