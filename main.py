import asyncio
import json
import random
import traceback

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from telethon import TelegramClient
from telethon.errors import UserDeactivatedBanError

import db.funcs as db
from client import Client
from config import DB_URL, logger
from proxies.proxy import Proxy


async def delay(coro, seconds):
    await asyncio.sleep(seconds)
    await coro


async def connect_sessions(*sessions):
    tasks = []
    for id, proxy_index in sessions:  # id - phone number
        with open(f'sessions/{id}/{id}.json') as f:
            data = json.load(f)
            app_id = data['app_id']
            app_hash = data['app_hash']
        session_path = f'sessions/{id}/{id}'

        try:
            proxy = Proxy(proxy_index)
            client = TelegramClient(session_path, app_id, app_hash,
                                    proxy=proxy.dict,
                                    device_model="iPhone 13 Pro Max",
                                    system_version="4.16.30-vxCUSTOM",
                                    app_version="8.4",
                                    lang_code="en",
                                    system_lang_code="en-US"
                                    )
            cli = Client(client, id)
        except UserDeactivatedBanError as ex:
            await db.set_banned_status(id)
            print(id)
            continue
        except Exception as ex:
            logger.info(traceback.format_exc())
            print(traceback.format_exc())
            print(id)

            continue

        tasks.append(
            asyncio.create_task(
                delay(cli.run(), random.randint(2, 5))
            )
        )
    return tasks


async def main():
    strange_sessions = ['17722807086', '17722807011', '17722807125']
    sessions = ['12097751806', '12097751810', '12097751858', '12097765573', '12098752242']
    sessions = [('12098898404', 0), ('12098898436', 1), ('12098898668', 2), ('12102692058', 3), ('12102738279', 4)]
    tasks = await connect_sessions(*sessions)
    await asyncio.wait(tasks)


asyncio.run(main())
