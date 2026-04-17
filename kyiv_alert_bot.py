import asyncio
import logging
import os
from telegram import Bot
from telegram.ext import Application, filters, MessageHandler, ContextTypes
import re
from datetime import datetime

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константи
BOT_TOKEN = os.getenv("BOT_TOKEN", "8333367228:AAH5VMN3AA__UtF8yASa4KCaMDVSrDFVb2w")
USER_ID = int(os.getenv("USER_ID", "636315061"))
CHANNEL_1 = "tryvoga_chomu"
CHANNEL_2 = "war_monitor"

# Ключові фрази для першого каналу
EXACT_PHRASES_CH1 = [
    "❗️Балістика на Київ",
    "❗️2х балістики на Київ",
    "💥Вибухи в Києві"
]

# Ключові фрази для другого каналу
EXACT_PHRASES_CH2 = [
    "☄ Вихід на Київ",
    "☄ Повторний на Київ",
    "‼️ Київ — спуск балістики!",
    "‼️ Київ — спуск балістики! Друга",
    "💥 Вибухи Київ, загроза балістики続續",
    "☄ Вихід у напрямку Київ"
]

# Регулярні вирази
PATTERN_CH1 = re.compile(
    r'(балістик[аи]|шахед[иы]?)\s+.*?(Київ[а]?)',
    re.IGNORECASE | re.DOTALL
)

PATTERN_CH2 = re.compile(
    r'(балістик[аи]|шахед[иы]?|кинжал[иы]?|ракет[аи])\s+.*?(Київ[а]?)',
    re.IGNORECASE | re.DOTALL
)

PATTERN_GENERAL = re.compile(
    r'((?:на|у напрямку|в напрямку)\s+)?Київ[а]?.*?(летит[ь]?|спуск|загроз|вибух)',
    re.IGNORECASE | re.DOTALL
)

async def check_alert(message_text, channel_name):
    """Перевіряє чи є в повідомленні ключові фрази"""
    
    if channel_name == CHANNEL_1:
        for phrase in EXACT_PHRASES_CH1:
            if phrase in message_text:
                return True
        if PATTERN_CH1.search(message_text):
            return True
    
    elif channel_name == CHANNEL_2:
        for phrase in EXACT_PHRASES_CH2:
            if phrase in message_text:
                return True
        if PATTERN_CH2.search(message_text):
            return True
        if PATTERN_GENERAL.search(message_text):
            return True
    
    return False

async def send_alert(bot, alert_text, channel):
    """Надсилає гучне сповіщення"""
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        alert_message = (
            f"🚨 <b>АЛЕРТ!</b> 🚨\n\n"
            f"Канал: <code>{channel}</code>\n"
            f"Час: <code>{timestamp}</code>\n\n"
            f"<b>Повідомлення:</b>\n"
            f"<pre>{alert_text[:500]}</pre>\n\n"
            f"⚠️ СПЕШІТЬ У УКРИТТЯ!"
        )
        
        await bot.send_message(
            chat_id=USER_ID,
            text=alert_message,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        logger.info(f"✅ Алерт надіслано! Канал: {channel}")
        
    except Exception as e:
        logger.error(f"❌ Помилка при надсиланні алерту: {e}")

async def handle_channel_message(update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє повідомлення з каналів"""
    
    try:
        if update.channel_post:
            message = update.channel_post
            message_text = message.text or message.caption or ""
            
            if message.chat and message.chat.username:
                channel_name = message.chat.username
                
                if channel_name in [CHANNEL_1, CHANNEL_2]:
                    logger.info(f"📨 Нове повідомлення з {channel_name}: {message_text[:100]}")
                    
                    if await check_alert(message_text, channel_name):
                        logger.warning(f"⚠️ АЛЕРТ ВИЯВЛЕНО! Канал: {channel_name}")
                        await send_alert(context.bot, message_text, channel_name)
    
    except Exception as e:
        logger.error(f"Помилка в обробці повідомлення: {e}")

async def post_init(application: Application) -> None:
    """Функція яка запускається після ініціалізації"""
    logger.info("✅ Бот запущено! Слідкую за каналами...")

def main():
    """Запуск бота"""
    
    logger.info("🤖 Запуск Kyiv Alert Bot...")
    
    try:
        # Створюємо додаток
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Встановлюємо post_init callback
        application.post_init = post_init
        
        # Додаємо обробник для повідомлень з каналів
        application.add_handler(
            MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_message)
        )
        
        # Запускаємо бота
        application.run_polling(allowed_updates=['channel_post'])
    
    except Exception as e:
        logger.error(f"❌ Критична помилка: {e}")
        raise

if __name__ == '__main__':
    main()
