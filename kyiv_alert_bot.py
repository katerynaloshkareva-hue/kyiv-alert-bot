import asyncio
import logging
import os
import re
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константи
API_ID = 36933179
API_HASH = "94abd4974e7058f3e5eac4efa27c91fa"
BOT_TOKEN = os.getenv("BOT_TOKEN", "8333367228:AAH5VMN3AA__UtF8yASa4KCaMDVSrDFVb2w")
USER_ID = int(os.getenv("USER_ID", "636315061"))
SESSION_NAME = "kyiv_alert_session"

# Канали для моніторингу
CHANNELS = ["tryvoga_chomu", "war_monitor"]

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
    
    if channel_name == "tryvoga_chomu":
        for phrase in EXACT_PHRASES_CH1:
            if phrase in message_text:
                return True
        if PATTERN_CH1.search(message_text):
            return True
    
    elif channel_name == "war_monitor":
        for phrase in EXACT_PHRASES_CH2:
            if phrase in message_text:
                return True
        if PATTERN_CH2.search(message_text):
            return True
        if PATTERN_GENERAL.search(message_text):
            return True
    
    return False

async def send_alert_via_bot(alert_text, channel_name):
    """Надсилає алерт через Telegram Bot API"""
    try:
        from telegram import Bot
        
        bot = Bot(token=BOT_TOKEN)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        alert_message = (
            f"🚨 <b>АЛЕРТ!</b> 🚨\n\n"
            f"Канал: <code>{channel_name}</code>\n"
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
        
        logger.info(f"✅ Алерт надіслано! Канал: {channel_name}")
        
    except Exception as e:
        logger.error(f"❌ Помилка при надсиланні алерту: {e}")

async def main():
    """Основна функція"""
    
    logger.info("🤖 Запуск Kyiv Alert Bot (Telethon Client)...")
    
    # Створюємо Telegram клієнт
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        # Підключаємося до Telegram
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Авторизовано як: {me.first_name} (@{me.username})")
        
        logger.info("✅ Бот запущено! Слідкую за каналами...")
        
        # Реєструємо обробник для нових повідомлень з каналів
        @client.on(events.NewMessage(chats=CHANNELS))
        async def handle_new_message(event):
            """Обробляє нові повідомлення з каналів"""
            try:
                message_text = event.message.text or ""
                
                # Отримуємо ім'я каналу
                chat = await event.get_chat()
                channel_name = chat.username or chat.title or "unknown"
                
                if not message_text:
                    return
                
                logger.info(f"📨 Нове повідомлення з @{channel_name}: {message_text[:100]}")
                
                # Перевіряємо на алерти
                if await check_alert(message_text, channel_name):
                    logger.warning(f"⚠️ АЛЕРТ ВИЯВЛЕНО! Канал: {channel_name}")
                    await send_alert_via_bot(message_text, channel_name)
            
            except Exception as e:
                logger.error(f"Помилка в обробці повідомлення: {e}")
        
        # Запускаємо слухача
        logger.info("🔍 Слухаю канали в реальному часі...")
        await client.run_until_disconnected()
        
    except SessionPasswordNeededError:
        logger.error("❌ Потрібна двофакторна аутентифікація. Запустіть вручну один раз.")
        raise
    
    except Exception as e:
        logger.error(f"❌ Критична помилка: {e}")
        raise
    
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
