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
    channels = ['+EmHan_WSvDdmNDky', '+PG9C65bK6_k3MDI6', '+ie1wo23VFH4xZmYy', 'aznakaevo', '+3ZEMGMfYaRs5M2Ji', 'bugulma', '+PPCMyxgyF5IwMTI6']
    sessions = ['12088371327', '12089645986', '12089997483', '12096217756']

    for i in range(len(sessions)):
        proxy_id = i % Proxy.proxy_count
        sessions[i] = (sessions[i], proxy_id, [channels[0]])
        if i // 2 == 0:
            sessions[i][2].extend(channels[1:4])
        else:
            sessions[i][2].extend(channels[4:])
    # sessions = sessions[1:2]
    # for i in range(len(sessions)):
    #     proxy_id = i % Proxy.proxy_count
    #     sessions[i] = (sessions[i], proxy_id, [channels[0], channels[i + 1]])

    channels1 = ['BybitRussian_News', 'slezisatoshi', 'prometheus', 'roflpuls', 'v_utushkin', 'don_invest', 'swoptoky_games', 'BogdanGdeX', 'dinar_banana', 'binance_ru']
    sessions1 = [['12096185207', 12, []], ['12095020282', 13, []], ['12107106097', 14, []]]

    for i in range(len(channels1)):
        sessions1[i % len(sessions1)][2].append(channels1[i])

    logger.info('test db ' + str(await db.get_client('12098898404')))
    print(sessions + sessions1)
    tasks = await connect_sessions(*(sessions1 + sessions))
    await asyncio.wait(tasks)


asyncio.run(main())
