import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, MessageReactionHandler

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8188816335:AAHnLxlKDfTvcH_ILzTZT81kTj9CRIpgEZo")

# Две группы для мониторинга
GROUP_1 = -1003276951156
GROUP_2 = -1003496475351
MONITORED_GROUPS = [GROUP_1, GROUP_2]

KEYWORD = "$$$"
TIMER_SECONDS = 60

async def check_and_forward(context: ContextTypes.DEFAULT_TYPE):
    """Пересылает сообщение в другую группу если нет реакций."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]
    
    # Определяем целевую группу (другая группа)
    target_group = GROUP_2 if chat_id == GROUP_1 else GROUP_1
    
    try:
        await context.bot.forward_message(
            chat_id=target_group,
            from_chat_id=chat_id,
            message_id=message_id
        )
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Сообщение {message_id} переслано из {chat_id} в {target_group} и удалено")
    except Exception as e:
        logger.error(f"Ошибка пересылки: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает сообщения с ключевым словом."""
    message = update.message
    if not message or not message.text:
        return
    
    logger.info(f"Сообщение от chat_id: {message.chat_id}, текст: {message.text}")
    
    if message.chat_id not in MONITORED_GROUPS:
        return
    
    if KEYWORD in message.text:
        logger.info(f"Обнаружено {KEYWORD} в сообщении {message.message_id}")
        context.job_queue.run_once(
            check_and_forward,
            TIMER_SECONDS,
            data={"chat_id": message.chat_id, "message_id": message.message_id},
            name=f"check_{message.chat_id}_{message.message_id}"
        )

async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет таймер при получении реакции."""
    if update.message_reaction:
        chat_id = update.message_reaction.chat.id
        message_id = update.message_reaction.message_id
        job_name = f"check_{chat_id}_{message_id}"
        
        jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in jobs:
            job.schedule_removal()
            logger.info(f"Таймер для сообщения {message_id} отменен (есть реакция)")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_message))
    app.add_handler(MessageReactionHandler(handle_reaction))
    
    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
