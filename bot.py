import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    MessageReactionHandler,
)

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Три группы для мониторинга
GROUP_1 = -1002228201497
GROUP_2 = -1002194287037
GROUP_3 = -4524185284  # ID третьей группы
MONITORED_GROUPS = [GROUP_1, GROUP_2, GROUP_3]

# Группа для проверки существования сообщений
CHECK_GROUP_ID = -1003262009283

KEYWORD = "$$$"
TIMER_SECONDS = 3600  # 60 минут
UPDATE_INTERVAL = 60  # Обновление таймера каждую минуту

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# Быстрое включение/выключение групп из ротации:
# - Через Railway Variables: ROTATION_ENABLED_GROUPS="-100...,-100...,-452..."
# - Или командами в CHECK_GROUP_ID: /enable <id>, /disable <id>, /status
ROTATION_ENABLED_GROUPS_ENV = os.getenv("ROTATION_ENABLED_GROUPS")

def _parse_enabled_groups(value: str | None) -> set[int] | None:
    if not value:
        return None
    out: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        out.add(int(part))
    return out

# Состояние на время работы процесса (команды меняют это без перезапуска)
enabled_groups_override: set[int] | None = _parse_enabled_groups(ROTATION_ENABLED_GROUPS_ENV)

def get_enabled_groups() -> list[int]:
    enabled = enabled_groups_override
    if enabled is None:
        return list(MONITORED_GROUPS)
    return [g for g in MONITORED_GROUPS if g in enabled]

def next_group(current_chat_id: int) -> int:
    enabled = get_enabled_groups()
    if not enabled:
        # если отключили всё - ротация невозможна, оставляем как есть
        return current_chat_id
    if current_chat_id not in enabled:
        return enabled[0]
    idx = enabled.index(current_chat_id)
    return enabled[(idx + 1) % len(enabled)]

def is_control_chat(update: Update) -> bool:
    return update.effective_chat is not None and update.effective_chat.id == CHECK_GROUP_ID

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_control_chat(update):
        return
    enabled = get_enabled_groups()
    await update.effective_message.reply_text(
        "Группы в ротации:\n"
        + "\n".join([f"- {gid}" for gid in enabled])
        + ("\n\n(ROTATION_ENABLED_GROUPS override активен)" if enabled_groups_override is not None else "")
    )

async def cmd_enable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global enabled_groups_override
    if not is_control_chat(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Использование: /enable <group_id>")
        return
    gid = int(context.args[0])
    if enabled_groups_override is None:
        enabled_groups_override = set(MONITORED_GROUPS)
    enabled_groups_override.add(gid)
    await cmd_status(update, context)

async def cmd_disable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global enabled_groups_override
    if not is_control_chat(update):
        return
    if not context.args:
        await update.effective_message.reply_text("Использование: /disable <group_id>")
        return
    gid = int(context.args[0])
    if enabled_groups_override is None:
        enabled_groups_override = set(MONITORED_GROUPS)
    enabled_groups_override.discard(gid)
    await cmd_status(update, context)

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global enabled_groups_override
    if not is_control_chat(update):
        return
    enabled_groups_override = _parse_enabled_groups(os.getenv("ROTATION_ENABLED_GROUPS"))
    await cmd_status(update, context)

async def update_timer(context: ContextTypes.DEFAULT_TYPE):
    """Обновляет сообщение с таймером."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    timer_message_id = job_data["timer_message_id"]
    original_message_id = job_data["original_message_id"]
    remaining = job_data["remaining"] - UPDATE_INTERVAL
    
    if remaining <= 0:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=timer_message_id)
        except:
            pass
        return
    
    # Проверяем существует ли оригинальное сообщение
    if CHECK_GROUP_ID:
        try:
            # Пробуем переслать в приватную группу для проверки
            check_msg = await context.bot.forward_message(
                chat_id=CHECK_GROUP_ID,
                from_chat_id=chat_id,
                message_id=original_message_id
            )
            await context.bot.delete_message(chat_id=CHECK_GROUP_ID, message_id=check_msg.message_id)
        except Exception as e:
            if "message" in str(e).lower() and "not found" in str(e).lower():
                # Оригинальное сообщение удалено - удаляем таймер и отменяем задачи
                logger.info(f"Сообщение {original_message_id} удалено, отменяем таймер")
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=timer_message_id)
                except:
                    pass
                # Отменяем основной таймер пересылки
                jobs = context.job_queue.get_jobs_by_name(f"check_{chat_id}_{original_message_id}")
                for job in jobs:
                    job.schedule_removal()
                return
    
    job_data["remaining"] = remaining
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=timer_message_id,
            text=f"⏱ Осталось {remaining // 60} мин для реакции"
        )
        # Планируем следующее обновление
        context.job_queue.run_once(
            update_timer,
            UPDATE_INTERVAL,
            data=job_data,
            name=f"timer_{chat_id}_{original_message_id}"
        )
    except Exception as e:
        logger.error(f"Ошибка обновления таймера: {e}")

async def check_and_forward(context: ContextTypes.DEFAULT_TYPE):
    """Пересылает сообщение в другую группу если нет реакций."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]
    timer_message_id = job_data.get("timer_message_id")
    
    # Удаляем сообщение таймера
    if timer_message_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=timer_message_id)
        except:
            pass
    
    # Отменяем задачи обновления таймера
    timer_jobs = context.job_queue.get_jobs_by_name(f"timer_{chat_id}_{message_id}")
    for job in timer_jobs:
        job.schedule_removal()
    
    # Определяем целевую группу с учетом выключенных групп
    target_group = next_group(chat_id)
    
    try:
        forwarded = await context.bot.forward_message(
            chat_id=target_group,
            from_chat_id=chat_id,
            message_id=message_id
        )
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Сообщение {message_id} переслано из {chat_id} в {target_group} и удалено")
    except Exception as e:
        # Сообщение уже удалено - просто выходим
        if "message to forward not found" in str(e).lower() or "message not found" in str(e).lower():
            logger.info(f"Сообщение {message_id} уже удалено, пропускаем")
            return
        raise e
    
    # Отправляем таймер для пересланного сообщения
    timer_msg = await context.bot.send_message(
        chat_id=target_group,
        text=f"⏱ Осталось {TIMER_SECONDS // 60} мин для реакции",
        reply_to_message_id=forwarded.message_id
    )
    
    # Запускаем обновление таймера
    timer_data = {
        "chat_id": target_group,
        "timer_message_id": timer_msg.message_id,
        "original_message_id": forwarded.message_id,
        "remaining": TIMER_SECONDS
    }
    context.job_queue.run_once(
        update_timer,
        UPDATE_INTERVAL,
        data=timer_data,
        name=f"timer_{target_group}_{forwarded.message_id}"
    )
    
    # Запускаем таймер для пересланного сообщения
    context.job_queue.run_once(
        check_and_forward,
        TIMER_SECONDS,
        data={"chat_id": target_group, "message_id": forwarded.message_id, "timer_message_id": timer_msg.message_id},
        name=f"check_{target_group}_{forwarded.message_id}"
    )
    logger.info(f"Таймер запущен для пересланного сообщения {forwarded.message_id}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает сообщения с ключевым словом в группах и каналах."""
    # effective_message работает и для групп (message), и для каналов (channel_post)
    message = update.effective_message
    if not message or not message.text:
        return
    
    logger.info(f"Сообщение от chat_id: {message.chat_id}, текст: {message.text}")
    
    if message.chat_id not in get_enabled_groups():
        return
    
    if KEYWORD in message.text:
        logger.info(f"Обнаружено {KEYWORD} в сообщении {message.message_id}")
        
        # Отправляем сообщение с таймером
        timer_msg = await context.bot.send_message(
            chat_id=message.chat_id,
            text=f"⏱ Осталось {TIMER_SECONDS // 60} мин для реакции",
            reply_to_message_id=message.message_id
        )
        
        # Запускаем обновление таймера
        timer_data = {
            "chat_id": message.chat_id,
            "timer_message_id": timer_msg.message_id,
            "original_message_id": message.message_id,
            "remaining": TIMER_SECONDS
        }
        context.job_queue.run_once(
            update_timer,
            UPDATE_INTERVAL,
            data=timer_data,
            name=f"timer_{message.chat_id}_{message.message_id}"
        )
        
        # Запускаем основной таймер
        context.job_queue.run_once(
            check_and_forward,
            TIMER_SECONDS,
            data={"chat_id": message.chat_id, "message_id": message.message_id, "timer_message_id": timer_msg.message_id},
            name=f"check_{message.chat_id}_{message.message_id}"
        )

async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет таймер при получении реакции."""
    if update.message_reaction:
        chat_id = update.message_reaction.chat.id
        message_id = update.message_reaction.message_id
        
        # Отменяем основной таймер
        job_name = f"check_{chat_id}_{message_id}"
        jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in jobs:
            # Удаляем сообщение таймера
            timer_message_id = job.data.get("timer_message_id")
            if timer_message_id:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=timer_message_id)
                except:
                    pass
            job.schedule_removal()
            logger.info(f"Таймер для сообщения {message_id} отменен (есть реакция)")
        
        # Отменяем задачи обновления таймера
        timer_jobs = context.job_queue.get_jobs_by_name(f"timer_{chat_id}_{message_id}")
        for job in timer_jobs:
            job.schedule_removal()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды управления (работают только в CHECK_GROUP_ID)
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("enable", cmd_enable))
    app.add_handler(CommandHandler("disable", cmd_disable))
    app.add_handler(CommandHandler("reset", cmd_reset))

    # Обрабатываем текст и в группах, и в каналах
    app.add_handler(MessageHandler(filters.TEXT & (filters.ChatType.GROUPS | filters.ChatType.CHANNEL), handle_message))
    app.add_handler(MessageReactionHandler(handle_reaction))
    
    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
