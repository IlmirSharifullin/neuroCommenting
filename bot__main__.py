import logging
import traceback

import asyncio
import requests
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import ErrorEvent
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot.config import BOT_TOKEN, BASE_WEBHOOK_URL, WEBHOOK_PATH, WEBHOOK_SECRET, LOGS_CHANNEL_ID, \
    WEB_SERVER_HOST, WEB_SERVER_PORT
from bot.handlers import callbacks, commands, messages


async def on_startup(bot: Bot):
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()


async def main():
    logging.basicConfig(
        filename='logs.log',
        format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s  ',
        datefmt='%d-%b-%y %H:%M:%S',
        level=logging.INFO
    )

    dp = Dispatcher()

    dp.include_routers(callbacks.router, commands.router, messages.router)

    @dp.error()
    async def error_handler(event: ErrorEvent):
        logging.error(traceback.format_exc())
        print(traceback.format_exc())
        res = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
                            params={'chat_id': LOGS_CHANNEL_ID, 'text': traceback.format_exc()[-2000:]})

    # Register startup hook to initialize webhook
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Create aiohttp.web.Application instance
    app = web.Application()

    # Create an instance of request handler,
    # aiogram has few implementations for different cases of usage
    # In this example we use SimpleRequestHandler which is designed to handle simple cases
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)
    # And finally start webserver
    return app


if __name__ == "__main__":
    running_sessions = []

    bot = Bot(BOT_TOKEN, parse_mode='')
    app = asyncio.run(main())

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
