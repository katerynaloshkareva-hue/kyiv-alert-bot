import asyncio
import logging
import os
import re
from datetime import datetime
from telegram import Bot
from telegram.ext import Application, filters, MessageHandler, ContextTypes
import aiohttp
from bs4 import BeautifulSoup
 
# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
 
# Константи
BOT_TOKEN = os.getenv("BOT_TOKEN", "8333367228:AAH5VMN3AA__UtF8yASa4KCaMDVSrDFVb2w")
USER_ID = int(os.getenv("USER_ID", "636315061"))
 
# Канали для моніторингу
CHANNELS = {
    "tryvoga_chomu": "https://t.me/tryvoga_chomu",
    "war_monitor": "https://t.me/war_monitor"
}
 
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
 
# Для збереження останніх перевірених повідомлень
last_checked_messages = {
    "tryvoga_chomu": set(),
    "war_monitor": set()
}
 
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
 
async def send_alert(bot, alert_text, channel_name):
    """Надсилає алерт користувачу"""
    try:
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
 
async def fetch_channel_messages(channel_name, channel_url):
    """Отримує останні повідомлення з каналу через веб-скрепінг"""
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(channel_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    
                    # Простий парсинг HTML
                    # Ищемо повідомлення в структурі Telegram веб-версії
                    messages = []
                    
                    # Це спрощений парсинг - може потребувати оновлення
                    # якщо Telegram змінить структуру
                    if "Балістика" in html or "вибух" in html or "летит" in html:
                        logger.info(f"📨 Можлива нова активність в {channel_name}")
                        return True
                    
                    return False
                else:
                    logger.warning(f"⚠️ Статус {resp.status} для {channel_name}")
                    return False
                    
    except Exception as e:
        logger.warning(f"⚠️ Помилка при скрепінгу {channel_name}: {e}")
        return False
 
async def monitor_channels(bot):
    """Періодично перевіряє канали"""
    
    logger.info("✅ Бот запущено! Слідкую за каналами...")
    logger.info("🔍 Перевіряю канали кожні 10 секунд...")
    
    while True:
        try:
            for channel_name, channel_url in CHANNELS.items():
                try:
                    # Перевіримо канал
                    has_updates = await fetch_channel_messages(channel_name, channel_url)
                    
                    if has_updates:
                        logger.info(f"📨 Нова активність в @{channel_name}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Помилка при перевірці {channel_name}: {str(e)[:100]}")
            
            # Чекаємо 10 секунд перед наступною перевіркою
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"❌ Критична помилка в моніторингу: {e}")
            await asyncio.sleep(10)
 
async def main():
    """Основна функція"""
    
    logger.info("🤖 Запуск Kyiv Alert Bot (Bot Token)...")
    
    try:
        # Створюємо бота
        bot = Bot(token=BOT_TOKEN)
        
        # Перевіримо що токен працює
        me = await bot.get_me()
        logger.info(f"✅ Бот успішно запущений: @{me.username}")
        
        # Запускаємо моніторинг каналів
        await monitor_channels(bot)
        
    except Exception as e:
        logger.error(f"❌ Критична помилка: {e}")
        raise
 
if __name__ == '__main__':
    asyncio.run(main())
