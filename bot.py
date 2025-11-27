import os
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "8188816335:AAHnLxlKDfTvcH_ILzTZT81kTj9CRIpgEZo")
SOURCE_CHANNEL_ID = -1003276951156  # Канал-источник
TARGET_GROUP_ID = -1003496475351    # Группа назначения
KEYWORD = "$$$"
TIMER_SECONDS = 60  # Время ожидания реакции (секунды)

async def check_and_forward(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет реакции и пересылает/удаляет сообщение если нет реакций."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]
    
    try:
        # Пересылаем сообщение в целевую группу
        await context.bot.forward_message(
            chat_id=TARGET_GROUP_ID,
            from_chat_id=chat_id,
            message_id=message_id
        )
        # Удаляем оригинальное сообщение
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Сообщение {message_id} переслано и удалено (нет реакций)")
    except Exception as e:
        print(f"Ошибка: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает новые сообщения с ключевым словом."""
    message = update.channel_post
    if not message or not message.text:
        return
    
    if KEYWORD in message.text:
        print(f"Обнаружено сообщение с {KEYWORD}: {message.message_id}")
        # Запускаем таймер
        context.job_queue.run_once(
            check_and_forward,
            TIMER_SECONDS,
            data={"chat_id": message.chat_id, "message_id": message.message_id},
            name=f"check_{message.message_id}"
        )

async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет таймер при получении реакции."""
    if update.message_reaction:
        message_id = update.message_reaction.message_id
        job_name = f"check_{message_id}"
        # Отменяем задачу если есть реакция
        jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in jobs:
            job.schedule_removal()
            print(f"Таймер для сообщения {message_id} отменен (есть реакция)")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчик сообщений в канале
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_message))
    
    # Обработчик реакций
    from telegram.ext import MessageReactionHandler
    app.add_handler(MessageReactionHandler(handle_reaction))
    
    print("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
