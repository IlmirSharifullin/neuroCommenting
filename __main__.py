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
                delay(cli.run(), proxy_index * random.randint(5, 10))
            )
        )
        await asyncio.sleep(5)
    return tasks


async def main():
    channels = ['+EmHan_WSvDdmNDky', '+PG9C65bK6_k3MDI6', '+ie1wo23VFH4xZmYy', 'aznakaevo', '+3ZEMGMfYaRs5M2Ji', 'bugulma', '+NpWaJ_fvj5c1NTdi']
    sessions = ['12098898404', '12098898436', '12098898668', '12102692058', '12102738279', '12105738318', '12107103112', '12107103242', '12107103256', '12133785331', '12109565013', '12132348393']
    # for i in range(len(sessions)):
    #     proxy_id = i % Proxy.proxy_count
    #     sessions[i] = (sessions[i], proxy_id, [channels[0], channels[i//2 + 1]])
    sessions = sessions[:6]
    for i in range(len(sessions)):
        proxy_id = i % Proxy.proxy_count
        sessions[i] = (sessions[i], proxy_id, [channels[0], channels[i + 1]])

    logger.info('test db ' + str(await db.get_client('12098898404')))

    tasks = await connect_sessions(*sessions)
    await asyncio.wait(tasks)


asyncio.run(main())
