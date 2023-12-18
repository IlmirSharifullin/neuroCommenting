import asyncio
import json
import os
import random
import time
import traceback

import telethon.errors
from telethon import TelegramClient, functions
from telethon.errors import UserDeactivatedBanError, UserAlreadyParticipantError
from telethon.tl.functions.messages import CheckChatInviteRequest

import db.funcs as db
from client import Client
from config import DB_URL, logger, log_to_channel
from proxies.proxy import Proxy

import shutil


async def is_subscribed(channel_link):
    res = await client(CheckChatInviteRequest(channel_link))
    print(res)
    try:
        await client.get_entity(channel_link)
        print('Subscribed')
        return True
    except Exception as e:
        print(e)
        if 'you are not part of' in str(e):
            return False

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
                delay(cli.run(), random.randint(5, 10))
            )
        )
    return tasks


async def main():
    # os.getcwd()
    # session_ids = os.listdir(os.getcwd() + '/sessions')
    # print(session_ids)
    # for proxy_id, session_id in enumerate(session_ids):
    #     proxy_id = proxy_id % 12
    #     print(session_id)
    #     from_db = await db.get_client(session_id)
    #     print(from_db)
    #     if from_db and from_db.status == db.ClientStatusEnum.USING.value:
    #         print('using')
    #         continue
    #     try:
    #         myCli = Client(session_id, proxy_id, [])
    #         async with myCli.client:
    #             try:
    #                 await asyncio.sleep(1)
    #                 me = await myCli.client.get_me()
    #             except Exception as ex:
    #                 print(ex)
    #                 await db.set_status(session_id, db.ClientStatusEnum.BANNED)
    #                 shutil.move(f'sessions/{session_id}', 'sessions_banned/')
    #                 print('banned')
    #             else:
    #                 await db.set_status(session_id, db.ClientStatusEnum.FREE)
    #                 await myCli.set_random_data()
    #                 print('new')
    #             await asyncio.sleep(2)
    #     except Exception as ex:
    #         print(traceback.format_exc())
    #         continue
    pass


# asyncio.run(main())
