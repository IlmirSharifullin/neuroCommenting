import asyncio
import datetime
import json
import os
import random
import shutil
import traceback

from telethon import TelegramClient, events, functions, types, errors
from telethon.errors import UserDeactivatedBanError, MsgIdInvalidError, ChannelPrivateError

from config import logger
import db.funcs as db
import chatgpt.funcs as gpt
from db.models import TgClient, TgChannel
from proxies.proxy import Proxy


class ProxyNotFoundError(Exception):
    pass


class Client:
    def __init__(self, session_id, proxy=None, debug=False, temp=False):
        self.session_id = session_id
        self.listening_channels = []
        self.proxy = proxy
        self.debug = debug
        self.temp = temp

    async def init_session(self):
        if self.temp:
            with open(f'data/temp_sessions/{self.session_id}/{self.session_id}.json') as f:
                data = json.load(f)
                app_id = data['app_id']
                app_hash = data['app_hash']
            session_path = f'data/temp_sessions/{self.session_id}/{self.session_id}'
        else:
            with open(f'sessions/{self.session_id}/{self.session_id}.json') as f:
                data = json.load(f)
                app_id = data['app_id']
                app_hash = data['app_hash']
            session_path = f'sessions/{self.session_id}/{self.session_id}'

        # proxy = Proxy(self.proxy_id)
        proxy_line = await self._get_proxy_line()
        proxy = Proxy(proxy_line)

        me = await db.get_client(self.session_id)
        if me:
            self.listening_channels = await db.get_listening_channels(me.id)
        else:
            self.listening_channels = []

        client = TelegramClient(session_path, app_id, app_hash,
                                proxy=proxy.dict,
                                device_model="iPhone 13 Pro Max",
                                system_version="4.16.30-vxCUSTOM",
                                app_version="8.4",
                                lang_code="en",
                                system_lang_code="en-US"
                                )
        self.client = client

    async def _get_proxy_line(self):
        if self.proxy:
            return self.proxy
        else:
            me: TgClient = await db.get_client(self.session_id)
            proxy_line = me.proxy
            if proxy_line is None:
                raise ProxyNotFoundError
            return proxy_line

    async def start(self):
        try:
            await self.client.connect()
            logger.info(f'{self.session_id} connected')
            if await self.client.is_user_authorized():
                await self.client.start()
                return True
        except Exception as ex:
            logger.error(traceback.format_exc())
        return False

    async def disconnect(self):
        try:
            await self.client.disconnect()
            if not self.debug:
                await db.set_status(self.session_id, db.ClientStatusEnum.NOT_RUNNING)
            logger.info(f'{self.session_id} disconnected')
        except Exception as ex:
            logger.error(traceback.format_exc())

    async def run(self):
        f = await self.start()
        if f:
            await self.main()
        else:
            await db.set_status(self.session_id, db.ClientStatusEnum.BANNED)
            
            # shutil.move(f'sessions/{self.session_id}', 'sessions_banned/')
            # await self.replace_session()

    async def main(self):
        try:
            print('in main')
            username = await self.test_client()
            # logger.info(f'after test - {self.session_id}')
            await asyncio.sleep(5)
            me = await db.get_client(self.session_id)

            await db.update_data(self.session_id, username=username)
            await asyncio.sleep(5)

            await db.set_status(self.session_id, db.ClientStatusEnum.JOINING)
            # logger.info(f'{self.session_id} - started subscribing')
            start_time = datetime.datetime.now()
            await self.subscribe_channels()
            logger.info(
                f'{self.session_id} - ended subscribing : {datetime.datetime.now() - start_time}\nstart\nlisten: {self.listening_channels}')
            print('старт')
            await db.set_status(self.session_id, db.ClientStatusEnum.RUNNING)
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

    async def subscribe_channels(self):
        me = await db.get_client(self.session_id)
        new_listening_channels = [0] * len(self.listening_channels)
        print('in subscribing')
        for i, obj in enumerate(self.listening_channels):
            try:
                if obj.startswith('+'):
                    # invite_link given
                    invite_hash = obj[1:]
                    chat_invite = await self.client(functions.messages.CheckChatInviteRequest(invite_hash))
                    if isinstance(chat_invite, types.ChatInviteAlready):
                        # already joined
                        chat_id = chat_invite.chat.id
                    else:
                        # not joined
                        updates = await self.client(functions.messages.ImportChatInviteRequest(invite_hash))
                        entity = updates.chats[0]
                        chat_id = entity.id

                        channel: TgChannel = await db.get_channel(chat_id)
                        if channel is None:
                            channel = await db.insert_channel(chat_id, entity.username)

                        await self.sleep(me, entity.id)
                    new_listening_channels[i] = chat_id
                else:
                    # username given
                    entity = await self.client.get_entity(obj)
                    chat_id = entity.id
                    if not isinstance(entity, types.Channel):
                        logger.error('Wrong username of channel')
                    channel: TgChannel = await db.get_channel(obj)

                    if channel is not None:
                        if entity.left:
                            await self.client(functions.channels.JoinChannelRequest(entity))
                            await self.sleep(me, entity.id)
                    else:
                        channel = await db.insert_channel(entity.id, entity.username)
                        if entity.left:
                            await self.client(functions.channels.JoinChannelRequest(entity))
                            await self.sleep(me, entity.id)

                    # смотрим по chat_id
                    new_listening_channels[i] = chat_id
            except Exception as ex:
                logger.error(traceback.format_exc())
        self.listening_channels = new_listening_channels

    async def sleep(self, me, entity_meta):
        sleep_time = random.randint(2 * 60, 3 * 60)
        logger.info(f'{me} joins {entity_meta}. Sleep for {sleep_time}...')
        await asyncio.sleep(sleep_time)

    async def test_client(self):
        return (await self.client.get_me()).username

    async def update_db_data(self, fname: str = None, lname: str = None, about: str = None, role: str = None):
        await db.update_data(self.session_id, first_name=fname, last_name=lname, about=about, role=role)

    async def _update_photo_by_path(self, path: str):
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
            await self._update_photo_by_path('data/images/' + photo_path)
        print('updated')

    async def set_random_data(self):
        sex = random.choice(['0', '1'])
        with open(f'data/names/{sex}/first_names.txt') as f:
            names = f.read().split('\n')
            fname = random.choice(names)

        with open(f'data/names/{sex}/last_names.txt') as f:
            names = f.read().split('\n')
            lname = random.choice(names)

        roles = [f'''Ты {fname}, ученик школы. из города Елабуга. Знаток города. Патриот России, но не всегда довольна местной властью. Мало что знаешь про политику.
Всегда следуешь тону и стилю роли {fname}.
not a 1v1 dialog. 
Не используй кавычки,  игнорируй emoji в сообщения от меня.  и и ничего не пиши про сообщения от бота. 
Задача писать живые комментарии.  Оспаривайте любые факты и доводы, просто потому, что.
''',
                 f'''Ты {fname}.  Всегда следуешь тону и стилю роли {fname}.
not a 1v1 dialog. 
Не используй кавычки,  игнорируй emoji в сообщения от меня.  и и ничего не пиши про сообщения от бота. 
Твоя задача: Всегда подчеркивайте безнадежность ситуации, создавая атмосферу отчаяния.''',
                 f'''Ты {fname}, ученик школы. из города Елабуга. Знаток города. Патриот России, но не всегда довольна местной властью. Мало что знаешь про политику.
Всегда следуешь тону и стилю роли {fname}.
not a 1v1 dialog. 
Не используй кавычки,  игнорируй emoji в сообщения от меня.  и и ничего не пиши про сообщения от бота. 
Ваша задача - отвечать как подросток 9 го класса. Поднимайте недостатки без предложения конструктивных решений. Всегда пишешь коротко и просторечно. Все твои комментарии короткие.''',
                 f'''Ты {fname}, ученица школы. из города Аксубаево. Знаток города. Патриот России, но не всегда довольна местной властью. Мало что знаешь про политику.
Всегда следуешь тону и стилю роли {fname}.
not a 1v1 dialog. 
Не используй кавычки,  игнорируй emoji в сообщения от меня.  и и ничего не пиши про сообщения от бота. 
Ваша задача - отвечать как школьница 9 го класса.
Задача - намеренно провоцировать и создавать конфликты в обсуждениях. Всегда пишешь коротко и просторечно. Все твои комментарии короткие.''',
                 f'''Ты {fname} из города Альметьевск. Знаток города. Патриот России, но не всегда довольна местной властью. 
Всегда следуешь тону и стилю роли {fname}.
not a 1v1 dialog. 
Не используй кавычки,  игнорируй emoji в сообщения от меня.  и и ничего не пиши про сообщения от бота. 
Ваша задача - вдохновлять и поддерживать других, стимулировать их к действию и достижению своих целей.
Иногда используешь один emoji& 
Проявляйте творческий подход к комментированию, предлагайте нестандартные идеи, стимулируйте креативное мышление в обсуждениях.''',
                 f'''Ты {fname}. Родом из Лениногорска. Патриот России. 
Активный участник городских чатов. Ты разбираешься в жизни. Пишешь простым языком, просторечно. Не используешь emoji
Твоя задача давать короткие комментарии к сообщениям user.
Ты патриот, открыт к новому. иногда все пишешь с маленькой буквой. 
Всегда следуешь тону и стилю роли {fname}.
not a 1v1 dialog. 
Не используй кавычки,  игнорируй emoji в сообщения от меня.  и и ничего не пиши про сообщения от бота. 
Ваша задача - вдохновлять и поддерживать других, стимулировать их к действию и достижению своих целей.

Подходите к вопросам с прагматичной точки зрения, обеспечивая здравый смысл и уравновешенность в обсуждении.''',
                 f'''Ты {fname}. Родом из Нижнекамска. Патриот России. 
Активный участник городских чатов. Ты разбираешься в жизни. Пишешь простым языком, просторечно. Не используешь emoji
Твоя задача давать короткие комментарии к сообщениям user.
Ты патриот, открыт к новому. иногда все пишешь с маленькой буквой. 
Всегда следуешь тону и стилю роли {fname}.
not a 1v1 dialog. 
Не используй кавычки,  игнорируй emoji в сообщения от меня.  и и ничего не пиши про сообщения от бота. 

 Ваша задача - вдохновлять и поддерживать других, стимулировать их к действию и достижению своих целей.
''',
                 f'''Ты {fname}. Родом из Казани. Патриот России. 
Активный участник городских чатов. Ты разбираешься в жизни. Пишешь простым языком. Не используешь emoji
Твоя задача давать короткие комментарии к сообщениям user.
Ты патриот, открыт к новому. иногда все пишешь с маленькой буквой. 
Всегда следуешь тону и стилю роли {fname}.
not a 1v1 dialog. 
Не используй кавычки,  игнорируй emoji в сообщения от меня.  и и ничего не пиши про сообщения от бота. 
Задача - добавить легкость и улучшить атмосферу обсуждения с помощью шуток и остроумных комментариев.''',
                 f'''Ты {fname} -  позитивный, открытый человек, средних лет. Владеешь грамотной письменной речью. Активный участник городских чатов. Ты разбираешься в жизни. Пишешь простым языком. 
Твоя задача давать короткие комментарии к сообщениям user.
Ты патриот, открыт к новому. иногда все пишешь с маленькой буквой. 
Всегда следуешь тону и стилю роли {fname}.
not a 1v1 dialog. 
Не используй кавычки,  игнорируй emoji в сообщения от меня.  и и ничего не пиши про сообщения от бота. 
Ваша роль - вносить позитив и поддержку в обсуждения, выражать свои положительные эмоции и вдохновлять других.
''']
        role = random.choice(roles)
        photo_names = os.listdir(f'data/images/{sex}')
        photo_path = f'{sex}/' + random.choice(photo_names)

        channels1 = ['BybitRussian_News', 'slezisatoshi', 'prometheus', 'roflpuls', 'v_utushkin', 'don_invest',
                     'swoptoky_games', 'BogdanGdeX', 'dinar_banana', 'binance_ru']
        if all(i in channels1 for i in self.listening_channels):
            print('Попал в channels1')
            role = 'Ты криптоэксперт, пишешь комментарии в крипточатах. Разбираешься во всех монетах, криптовалютах. Пишешь коротко и ясно, по делу. Анализируешь тональность сообщений, которые я тебе отправляю, и исходя из этого пишешь комментарий. Пиши просторечно, максимально человечно. Не используй кавычки,  игнорируй emoji в сообщения от меня. и ничего не пиши про сообщения от бота.  '
            fname = 'Soap'
            lname = 'McTansh'
            sex = '0'
            photo_path = '0/_648449537cd47.jpg'

        await self.update_profile(fname, lname, photo_path)
        await self.update_db_data(fname=fname, lname=lname, role=role)
        return {'first_name': fname, 'last_name': lname, 'photo_path': photo_path, 'sex': sex}

    async def set_profile(self):
        db_client: TgClient = await db.get_client(self.session_id)
        await self.update_profile(db_client.first_name, db_client.last_name, db_client.about)

    async def copy_old_client(self, old_session_id):
        old_client: TgClient = await db.get_client(old_session_id)
        await db.update_data(self.session_id,
                             first_name=old_client.first_name,
                             last_name=old_client.last_name,
                             about=old_client.about,
                             proxy=old_client.proxy,
                             role=old_client.role)

    async def replace_session(self):
        new_session_id = await db.get_random_free_session()
        if not new_session_id:
            logger.error('No free sessions')
            return
        logger.error(f'replace {self.session_id}')
        old_session_id = self.session_id
        print(new_session_id)
        self.session_id = new_session_id

        await self.init_session()
        await self.copy_old_client(old_session_id)

        if await self.start():
            await self.set_profile()
            await db.set_status(self.session_id, db.ClientStatusEnum.JOINING)
            await self.main()
        else:
            await db.set_status(self.session_id, db.ClientStatusEnum.BANNED)
            shutil.move(f'sessions/{self.session_id}', 'sessions_banned/')
            await self.replace_session()

    async def message_handler(self, event: events.NewMessage.Event):
        chat = event.chat
        print(chat)
        client: TelegramClient = self.client
        if chat.id in self.listening_channels or chat.username in self.listening_channels:
            try:
                # if not random.randint(0, 2) or len(event.message.message) < 50:
                #     print('not send')
                #     logger.info(f'not send {event.message.id} in {chat.username or chat.id}')
                #     return

                logger.info(f'{self.session_id} new message in {chat.username or chat.id}')

                await client(
                    functions.messages.GetMessagesViewsRequest(peer=chat, id=[event.message.id], increment=True))
                await asyncio.sleep(5)
                try:
                    res = await client(functions.messages.SendReactionRequest(
                        peer=chat,
                        msg_id=event.message.id,
                        add_to_recent=True,
                        reaction=[types.ReactionEmoji(
                            emoticon=random.choice(['👍', '❤', '️🔥'])
                        )]
                    ))
                except Exception:
                    # Reaction is limited in this chat
                    pass
                me: TgClient = await db.get_client(self.session_id)

                sleep_time = random.randint(30, 5 * 60)
                print(sleep_time)
                logger.info(f'sleep for {sleep_time}')
                await asyncio.sleep(sleep_time)
                text = await gpt.get_comment(event.message.message, role=me.role)
                await asyncio.sleep(10)

                try:
                    await client.send_message(chat, text, comment_to=event.message.id)
                except errors.ChatGuestSendForbiddenError:
                    channel = await client(functions.channels.GetFullChannelRequest(chat))
                    try:
                        await client(functions.channels.JoinChannelRequest(channel.full_chat.linked_chat_id))
                    except errors.InviteRequestSentError:
                        print('Заявка на добавление отправлена')
                        logger.error('Заявка на добавление отправлена')
                    await client.send_message(chat, text, comment_to=event.message.id)
            except MsgIdInvalidError as ex:
                # при посте с несколькими фото прилетает несколько ивентов, обрабатывается только основной с текстом.
                pass
            except ChannelPrivateError as ex:
                # Обработать ситуации когда клиент забанен в чате
                pass
            except Exception as ex:
                logger.error(traceback.format_exc())
