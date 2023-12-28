import asyncio
import json
import random
import time
import traceback

from telethon import TelegramClient
from telethon.errors import UserDeactivatedBanError

import db.funcs as db
from client import Client
from config import DB_URL, logger, log_to_channel
from proxies.proxy import Proxy


async def delay(coro, seconds):
    await asyncio.sleep(seconds)
    await coro


async def connect_sessions(*sessions):
    tasks = []
    for session_id, proxy_index, listening_channels in sessions:
        try:
            cli = Client(session_id, proxy_index, listening_channels)
        except UserDeactivatedBanError as ex:
            await db.set_status(session_id, db.ClientStatusEnum.BANNED)
            print(session_id)
            continue
        except Exception as ex:
            logger.error(traceback.format_exc())
            print(session_id)

            continue

        tasks.append(
            asyncio.create_task(
                delay(cli.run(), random.randint(5, 10))
            )
        )
        await asyncio.sleep(5)
    return tasks


async def main():
    channels = ['+EmHan_WSvDdmNDky']
    client = Client('12096185207', debug=True)
    await client.init_session()
    await client.run()

asyncio.run(main())
