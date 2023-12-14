import asyncio
import json
import random
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
    return tasks


async def main():
    sessions = [('12098898404', 0, ['+EmHan_WSvDdmNDky']), ('12098898436', 1, ['+EmHan_WSvDdmNDky', '+9Q4o4muW2kxkMzky']), ('12098898668', 2), ('12102692058', 3), ('12102738279', 4), ("13527688414")]
    sessions = sessions[1:2]
    logger.info('test db ' + str(await db.get_client('12098898404')))

    tasks = await connect_sessions(*sessions)
    await asyncio.wait(tasks)


asyncio.run(main())
