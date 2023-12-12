import asyncio
import datetime
import os
import random
import traceback

from telethon import TelegramClient, events, functions, types
from telethon.errors import UserDeactivatedBanError

from config import channel_logins, logger, log_to_channel
import db.funcs as db
import chatgpt.funcs as gpt
from db.models import TgClient


class Client:
    def __init__(self, client: TelegramClient, session_id):
        self.client = client
        self.session_id = session_id

    async def run(self):
        try:
            test = await db.test()
            print(test)
            logger.info(test)
            logger.info(f"running {self.session_id}")
            await self.client.connect()
            logger.info(f'connected to {self.session_id}')
            me = await db.get_client(self.session_id)
            if me is None:
                await db.insert_client(self.session_id)
                me = await db.get_client(self.session_id)
            await asyncio.sleep(5)

            # await self.set_random_data()

            print(me.session_id)
            logger.info(f'{me.session_id} - started subscribing')
            start_time = datetime.datetime.now()
            await self.subscribe_channels()
            logger.info(f'{me.session_id} - ended subscribing : {datetime.datetime.now() - start_time}')
            print('старт')
            logger.info(f'start {self.session_id}')
            needs = True
            if needs:
                self.client.add_event_handler(self.message_handler, events.NewMessage())
            await self.client.run_until_disconnected()
        except Exception as ex:
            logger.error(traceback.format_exc())
            print(traceback.format_exc())
            await self.client.run_until_disconnected()
            await self.client.disconnect()
        except KeyboardInterrupt:
            await self.client.disconnect()

    async def subscribe_channels(self):
        try:
            me = await db.get_client(self.session_id)
            print(me)
            channels = await db.get_channels()
            channels_usernames = [channel.username for channel in channels]
            for username in channel_logins:
                entity = None
                if username not in channels_usernames:
                    print(username)
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
                        sleep_time = random.randint(10 * 60, 20 * 60)
                        print(f'{me} joins {username}. Sleep for {sleep_time}...')
                        await asyncio.sleep(sleep_time)

        except UserDeactivatedBanError as ex:
            await db.set_banned_status(self.session_id)
            log_to_channel(f'{self.session_id} client banned')
            print(self.session_id)
        except Exception as ex:
            logger.error(traceback.format_exc())
            print(ex)

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

    async def message_handler(self, event: events.NewMessage.Event):
        chat = event.chat
        session = self
        client: TelegramClient = session.client
        if chat.username in channel_logins[0:1]:
            try:
                if not random.randint(0, 1):
                    print('not send')
                    logger.info(f'not send {event.message.id} in {chat.username}')
                    return

                logger.info(f'new message in {chat.username}')
                print(chat.username)
                result = await client(functions.messages.SendReactionRequest(
                    peer=chat,
                    msg_id=event.message.id,
                    add_to_recent=True,
                    reaction=[types.ReactionEmoji(
                        emoticon=random.choice('👍❤️🔥')
                    )]
                ))
                print(result)
                me: TgClient = await db.get_client(session.session_id)

                await client(
                    functions.messages.GetMessagesViewsRequest(peer=chat, id=[event.message.id], increment=True))
                sleep_time = random.randint(30, 5 * 60)
                print(sleep_time)
                # await asyncio.sleep(sleep_time)
                text = await gpt.get_comment(event.message.message, sex=me.sex)
                print(text)
                await asyncio.sleep(10)
                await client.send_message(chat, text, comment_to=event.message.id)
            except Exception as ex:
                logger.error(traceback.format_exc())
                print(traceback.format_exc())
