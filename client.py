import asyncio
import datetime
import json
import os
import random
import shutil
import traceback
from typing import List

from telethon import TelegramClient, events, functions, types
from telethon.errors import UserDeactivatedBanError

from config import channel_logins, logger, log_to_channel
import db.funcs as db
import chatgpt.funcs as gpt
from db.models import TgClient, TgChannel
from proxies.proxy import Proxy


class Client:
    def __init__(self, session_id, proxy_id, listening_channels: List[str]):
        self.session_id = session_id
        self.proxy_id = proxy_id
        self.listening_channels = listening_channels

        self.init_session()

    def init_session(self):
        with open(f'sessions/{self.session_id}/{self.session_id}.json') as f:
            data = json.load(f)
            app_id = data['app_id']
            app_hash = data['app_hash']
        session_path = f'sessions/{self.session_id}/{self.session_id}'

        proxy = Proxy(self.proxy_id)

        client = TelegramClient(session_path, app_id, app_hash,
                                proxy=proxy.dict,
                                device_model="iPhone 13 Pro Max",
                                system_version="4.16.30-vxCUSTOM",
                                app_version="8.4",
                                lang_code="en",
                                system_lang_code="en-US"
                                )
        self.client = client

    async def start(self):
        try:
            await self.client.connect()
            logger.info('connect')
            if await self.client.is_user_authorized():
                await self.client.start()
                return True
        except Exception as ex:
            logger.error(traceback.format_exc())
        return False

    async def run(self):

        if await self.start():
            await self.main()
        else:

            shutil.move(f'sessions/{self.session_id}', 'sessions_banned/')
            await db.set_status(self.session_id, db.ClientStatusEnum.BANNED)
            await self.replace_session()

    async def main(self):
        try:
            log_to_channel(await db.get_client(self.session_id))
            await self.test_client()
            await db.set_status(self.session_id, db.ClientStatusEnum.USING)
            await asyncio.sleep(5)
            logger.info(f"running {self.session_id}")
            me = await db.get_client(self.session_id)
            if me is None:
                await db.insert_client(self.session_id)
                me = await db.get_client(self.session_id)
            await asyncio.sleep(5)

            # await self.set_random_data()

            logger.info(f'{self.session_id} - started subscribing')
            start_time = datetime.datetime.now()
            await self._subscribe_channels()
            logger.info(f'{self.session_id} - ended subscribing : {datetime.datetime.now() - start_time}')

            print('старт')
            logger.info(f'start {self.session_id}')

            needs = True
            if needs:
                self.client.add_event_handler(self.message_handler, events.NewMessage())
            await self.client.run_until_disconnected()
        except UserDeactivatedBanError:
            await db.set_status(self.session_id, db.ClientStatusEnum.BANNED)
            shutil.move(f'sessions/{self.session_id}', 'sessions_banned/')
            logger.info(f'{self.session_id} client banned')
            await self.replace_session()
        except Exception as ex:
            logger.error(traceback.format_exc())
            print(traceback.format_exc())

    async def subscribe_channels(self):
        me = await db.get_client(self.session_id)
        print(me)
        channels = await db.get_channels()
        channels_usernames = [channel.username for channel in channels]
        for username in self.listening_channels:
            entity = None
            if username not in channels_usernames:

                print(username)
                if isinstance(username, int):
                    continue
                await self.client(functions.messages.ImportChatInviteRequest())
                entity = await self.client.get_entity(username)
                channel = await db.insert_channel(entity.id, entity.username)
                channels_usernames.append(channel.username)
                print(channel)
            else:
                channel = await db.get_channel(username)

            joined_clients = await db.get_joined_clients(channel)
            if not joined_clients:
                joined_clients = []
            if me.id not in joined_clients:
                if channel:
                    if entity is None:
                        entity = await self.client.get_entity(username)
                    await self.client(functions.channels.JoinChannelRequest(entity))
                    await db.add_join(me, channel)
                    sleep_time = random.randint(5 * 60, 10 * 60)
                    print(f'{me} joins {username}. Sleep for {sleep_time}...')
                    await asyncio.sleep(sleep_time)

    async def _subscribe_channels(self):
        me = await db.get_client(self.session_id)
        for i, obj in enumerate(self.listening_channels):
            try:
                if obj.startswith('+'):
                    invite_link = obj[1:]
                    try:
                        entity = await self.client.get_entity(
                            'https://t.me/joinchat/' + invite_link)  # exists and joined
                    except Exception as ex:
                        if 'you are not part of' in str(ex):  # Exists but not joined
                            res1 = await self.client(functions.messages.ImportChatInviteRequest(invite_link))
                            entity = res1.chats[0]

                            channel: TgChannel = await db.get_channel(entity.id)
                            if channel is None:
                                channel = await db.insert_channel(entity.id, entity.username)
                            await db.add_join(me, channel)

                            sleep_time = random.randint(5 * 60, 10 * 60)
                            print(f'{me} joins {entity.id}. Sleep for {sleep_time}...')
                            await asyncio.sleep(sleep_time)
                        else:  # Not exists
                            logger.error(traceback.format_exc())
                            continue
                    print(entity)
                    self.listening_channels[i] = entity.id
                else:
                    joined_channels = await db.get_joined_channels(me)
                    channel: TgChannel = await db.get_channel(obj)
                    if channel is not None:
                        if channel.id not in [i.channel_id for i in joined_channels]:
                            # канал есть в бд, но юзер не подписан
                            entity = await self.client.get_entity(obj)
                            await self.client(functions.channels.JoinChannelRequest(entity))
                            await db.add_join(me, channel)

                            sleep_time = random.randint(5 * 60, 10 * 60)
                            print(f'{me} joins {entity.id}. Sleep for {sleep_time}...')
                            await asyncio.sleep(sleep_time)
                    else:
                        # канала нет в бд, нужно добавить
                        entity = await self.client.get_entity(obj)
                        if not isinstance(entity, types.Channel):
                            logger.error('Wrong username of channel')
                            continue

                        channel = await db.insert_channel(entity.id, entity.username)
                        await self.client(functions.channels.JoinChannelRequest(entity))
                        await db.add_join(me, channel)

                        sleep_time = random.randint(5 * 60, 10 * 60)
                        print(f'{me} joins {entity.id}. Sleep for {sleep_time}...')
                        await asyncio.sleep(sleep_time)
            except Exception as ex:
                logger.error(ex)

    async def test_client(self):
        print('test', await self.client.get_me())

    async def get_joined_channels(self):
        me = await db.get_client(self.session_id)
        return await db.get_joined_channels(me)

    async def update_db_data(self, fname: str = None, lname: str = None, sex: str = None, photo_path: str = None,
                             about: str = None):
        await db.update_data(self.session_id, first_name=fname, last_name=lname, sex=sex, photo_path=photo_path,
                             about=about)

    async def _update_photo(self, path: str):
        photo = await self.client.upload_file(path)
        photos = await self.client.get_profile_photos('me')
        for i in range(len(photos)):
            photos[i] = types.InputPhoto(
                id=photos[i].id,
                access_hash=photos[i].access_hash,
                file_reference=photos[i].file_reference
            )
        await self.client(functions.photos.DeletePhotosRequest(
            id=photos))

        return await self.client(functions.photos.UploadProfilePhotoRequest(file=photo))

    async def update_profile(self, fname: str = None, lname: str = None, photo_path: str = None, about: str = None):
        await self.client(functions.account.UpdateProfileRequest(first_name=fname, last_name=lname, about=about))
        if photo_path:
            await self._update_photo('data/images/' + photo_path)
        print('updated')

    async def set_random_data(self):
        sex = random.choice(['0', '1'])
        with open(f'data/names/{sex}/first_names.txt') as f:
            names = f.read().split('\n')
            fname = random.choice(names)

        with open(f'data/names/{sex}/last_names.txt') as f:
            names = f.read().split('\n')
            lname = random.choice(names)

        photo_names = os.listdir(f'data/images/{sex}')
        photo_path = f'{sex}/' + random.choice(photo_names)
        await self.update_profile(fname, lname, photo_path)
        await self.update_db_data(fname, lname, sex, photo_path)
        return {'first_name': fname, 'last_name': lname, 'photo_path': photo_path, 'sex': sex}

    async def set_profile(self):
        db_client: TgClient = await db.get_client(self.session_id)
        await self.update_profile(db_client.first_name, db_client.last_name, db_client.photo_path, db_client.about)

    async def copy_old_client(self, old_session_id):
        old_client: TgClient = await db.get_client(old_session_id)
        await db.update_data(self.session_id,
                             first_name=old_client.first_name,
                             last_name=old_client.last_name,
                             sex=old_client.sex,
                             photo_path=old_client.photo_path,
                             about=old_client.about,
                             role=old_client.role)

    async def set_listening_channels(self):
        pass

    async def replace_session(self):
        logger.error(f'replace {self.session_id}')
        new_session_id = await db.get_random_free_session()
        if not new_session_id:
            logger.error('No free sessions')
            return
        old_session_id = self.session_id
        print(new_session_id)
        self.session_id = new_session_id

        self.init_session()
        await self.copy_old_client(old_session_id)

        if await self.start():
            await self.set_profile()
            await db.set_status(self.session_id, db.ClientStatusEnum.USING)
            await self.main()
        else:
            await db.set_status(self.session_id, db.ClientStatusEnum.BANNED)
            shutil.move(f'sessions/{self.session_id}', 'sessions_banned/')
            await self.replace_session()

    async def message_handler(self, event: events.NewMessage.Event):
        chat = event.chat

        client: TelegramClient = self.client
        # print(chat)
        if chat.id in self.listening_channels or chat.username in self.listening_channels:
            try:
                # if not random.randint(0, 1):
                #     print('not send')
                #     logger.info(f'not send {event.message.id} in {chat.username or chat.id}')
                #     return

                logger.info(f'new message in {chat.username or chat.id}')

                await client(
                    functions.messages.GetMessagesViewsRequest(peer=chat, id=[event.message.id], increment=True))
                await asyncio.sleep(1)
                res = await client(functions.messages.SendReactionRequest(
                    peer=chat,
                    msg_id=event.message.id,
                    add_to_recent=True,
                    reaction=[types.ReactionEmoji(
                        emoticon=random.choice(['👍', '❤', '️🔥'])
                    )]
                ))

                me: TgClient = await db.get_client(self.session_id)

                sleep_time = random.randint(30, 5 * 60)
                print(sleep_time)
                await asyncio.sleep(sleep_time)

                text = await gpt.get_comment(event.message.message, role=me.role)
                print(text)
                await asyncio.sleep(10)
                await client.send_message(chat, text, comment_to=event.message.id)
            except Exception as ex:
                logger.error(traceback.format_exc())
                print(traceback.format_exc())
