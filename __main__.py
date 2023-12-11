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
            log_to_channel(traceback.format_exc())
            logger.info(traceback.format_exc())
            print(traceback.format_exc())
            print(id)

            continue

        tasks.append(
            asyncio.create_task(
                delay(cli.run(), random.randint(5, 10))
            )
        )
    return tasks


async def main():
    sessions = [('12098898404', 0), ('12098898436', 1), ('12098898668', 2), ('12102692058', 3), ('12102738279', 4)]
    sessions = sessions[1:-3]
    tasks = await connect_sessions(*sessions)
    await asyncio.wait(tasks)


asyncio.run(main())
