import traceback

from aiogram import Bot

from bot.config import BOT_TOKEN
from config import logger

bot = Bot(BOT_TOKEN)


async def notify_owner(owner_id: int, text: str):
    try:
        await bot.send_message(owner_id, text)
    except Exception:
        logger.error(traceback.format_exc())
