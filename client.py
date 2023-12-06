import asyncio
import datetime
import logging
import random
import time
import traceback
from functools import partial

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telethon import TelegramClient, events
from telethon.errors import UserDeactivatedBanError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.channels import ReadMessageContentsRequest
from telethon.tl.types import Channel, User

from config import channel_logins, logger
import db.funcs as db


async def message_handler(event: events.NewMessage.Event, client: TelegramClient):
    chat = event.chat
    choices = [
        'Вот это да!',
        'Интересно...',
        'Не отлично, но и не ужасно)',
        '👍',
        'Всем привет.'
    ]
    if chat.username in channel_logins:
        try:
            print(chat.username)
            await asyncio.sleep(random.randint(30, 5*60))
            await client.send_message(chat, random.choice(choices), comment_to=event.message.id)
            await asyncio.sleep(180)
        except Exception as ex:
            print(ex)
            pass


class Client:
    def __init__(self, client: TelegramClient, session_id):
        self.me = None
        self.client = client
        self.session_id = session_id

    async def run(self):
        await self.client.connect()

        self.me = await db.get_client(self.session_id)
        if self.me is None:
            self.me = await db.insert_client(self.session_id)
            print(self.me)
        await asyncio.sleep(5)
        # self.client.add_event_handler(partial(message_handler, client=self.client), events.NewMessage())

        logger.info(f'{self.me.session_id} - started subscribing')
        start_time = datetime.datetime.now()
        await self.subscribe_channels()
        logger.info(f'{self.me.session_id} - ended subscribing : {datetime.datetime.now() - start_time}')

        needs = False
        if needs:
            self.client.add_event_handler(partial(message_handler, client=self.client), events.NewMessage())
            await self.client.run_until_disconnected()
        else:
            await self.client.disconnect()

    async def subscribe_channels(self):
        try:
            channels = await db.get_channels()
            channels_usernames = [channel.username for channel in channels]
            for username in channel_logins:
                entity = None
                if username not in channels_usernames:
                    entity = await self.client.get_entity(username)
                    channel = await db.insert_channel(entity.username, entity.id)
                else:
                    channel = await db.get_channel(username)

                joined_clients = await db.get_joined_clients(channel)
                if self.me.id not in joined_clients:
                    if entity is None:
                        entity = await self.client.get_entity(username)
                    await self.client(JoinChannelRequest(entity))
                    await db.add_join(self.me, channel)
                    sleep_time = random.randint(10*60, 20*60)
                    print(f'{self.me} joins {channel.username}. Sleep for {sleep_time}...')
                    await asyncio.sleep(sleep_time)
        except UserDeactivatedBanError as ex:
            await db.set_banned_status(self.session_id)
            print(self.session_id)
        except Exception as ex:
            logger.error(traceback.format_exc())
            print(traceback.format_exc())

    async def get_joined_channels(self):
        return await db.get_joined_channels(self.me)
