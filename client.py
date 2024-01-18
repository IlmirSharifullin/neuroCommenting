import asyncio
import datetime
import json
import random
import shutil
import traceback

from telethon import TelegramClient, events, functions, types, errors
from telethon.errors import UserDeactivatedBanError, MsgIdInvalidError, ChannelPrivateError

from bot.notifications import notify_owner
from config import logger
import db.funcs as db
import chatgpt.funcs as gpt
from db.models import TgClient, TgChannel
from proxies.proxy import Proxy


class ProxyNotFoundError(Exception):
    pass


class Client:
    def __init__(self, session_id, proxy=None, debug=False, temp=False, changing=False):
        self.session_id = session_id
        self.listening_channels = []
        self.proxy = proxy
        self.debug = debug
        self.temp = temp
        self.changing = changing

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
        except ConnectionError as ex:
            await asyncio.sleep(30)
            return await self.start()
        except Exception as ex:
            logger.error(traceback.format_exc())
        return False

    async def disconnect(self):
        try:
            await self.client.disconnect()
            if not self.temp and not self.changing:
                await db.set_status(self.session_id, db.ClientStatusEnum.NOT_RUNNING)
            logger.info(f'{self.session_id} disconnected')
        except Exception as ex:
            logger.error(traceback.format_exc())

    async def run(self, restart=False):
        f = await self.start()
        if f:
            await self.main(restart=restart)
        else:
            if not self.changing:
                await db.set_status(self.session_id, db.ClientStatusEnum.BANNED)
                logger.error(f'{self.session_id} banned when start')
            # shutil.move(f'sessions/{self.session_id}', 'sessions_banned/')
            # await self.replace_session()

    async def main(self, restart=False):
        try:
            if not restart:
                print('in main')
                username = await self.test_client()
                # logger.info(f'after test - {self.session_id}')
                await asyncio.sleep(5)

                await db.update_data(self.session_id, username=username)
                await asyncio.sleep(5)

                await self.join_channels()

                await db.set_status(self.session_id, db.ClientStatusEnum.RUNNING)

            await self.set_handler()
        except UserDeactivatedBanError:
            await db.set_status(self.session_id, db.ClientStatusEnum.BANNED)
            shutil.move(f'sessions/{self.session_id}', 'sessions_banned/')
            logger.info(f'{self.session_id} banned while running')
            await self.replace_session()
        except ConnectionError:
            me = await db.get_client(self.session_id)
            # await notify_owner(me.owner_id,
            #                    'Ошибка при подключении к серверам Телеграма. Попробуем еще раз через минуту')
            await self.disconnect()
            await asyncio.sleep(5)
            # await notify_owner(me.owner_id, 'Пробуем снова')
            await self.run(restart=True)
        except Exception as ex:
            logger.error(traceback.format_exc())

    async def set_handler(self):
        self.client.remove_event_handler(self.message_handler)
        self.client.add_event_handler(self.message_handler, events.NewMessage())

        await self.client.run_until_disconnected()

    async def join_channels(self):
        me: TgClient = await db.get_client(self.session_id)

        await db.set_status(self.session_id, db.ClientStatusEnum.JOINING)
        # logger.info(f'{self.session_id} - started subscribing')
        start_time = datetime.datetime.now()
        await self.subscribe_channels()
        logger.info(
            f'{self.session_id} - ended subscribing : {datetime.datetime.now() - start_time}\nstart\nlisten: {self.listening_channels}')

        await notify_owner(me.owner_id,
                           f'{me} подписался на каналы и начал их прослушивать')

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
        return logger.error('Замена недоступна')
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
        client: TelegramClient = self.client

        await self.communication(event)

        if chat.id in self.listening_channels or chat.username in self.listening_channels:
            try:
                me: TgClient = await db.get_client(self.session_id)
                filename = None

                if event.message.id % me.answer_posts != 0:
                    logger.info(
                        f'{me.first_name} {me.last_name} not send {event.message.id} in {chat.username or chat.id}')
                    return

                # if isinstance(event.message.media,
                #               types.MessageMediaPhoto):  # является ли тип вложения сообщения фотографией
                #     filename = f'temp{datetime.datetime.now()}.jpg'
                #     await event.message.download_media(file=filename, thumb=-1)
                logger.info(f'{me.first_name} {me.last_name} new message in {chat.username or chat.title or chat.id}')

                sleep_time = random.randint(me.min_answer_time, me.max_answer_time)
                print(sleep_time)
                logger.info(f'{me.first_name} {me.last_name} sleeps for {sleep_time}')
                await asyncio.sleep(sleep_time)

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
                    # Reactions are limited in this chat
                    pass

                if me.is_neuro:
                    if not me.role:
                        return notify_owner(me.owner_id,
                                            f'Не указана роль у {me}. Комментарии не могут составляться без роли, можете переключить на режим Готовый Текст, нажав кнопку "Выключить нейросеть"')
                    text = await gpt.get_comment(event.message.message, role=me.role, photo_path=filename)
                else:
                    text = me.text
                await asyncio.sleep(10)
                # os.remove(filename)
                if me.is_premium and me.send_as is not None:
                    try:
                        await client(functions.messages.SaveDefaultSendAsRequest(chat, me.send_as))
                    except errors.SendAsPeerInvalidError:
                        # await notify_owner(me.owner_id,
                        #                    f'У аккаунта {me} указан неправильный юзернейм, от лица которого нужно писать комментарии')
                        pass
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
                if not self.debug:
                    db_me: TgClient = await db.get_client(self.session_id)
                    await notify_owner(db_me.owner_id,
                                       f'Сессию {db_me.username} {db_me.first_name} {db_me.last_name} забанили в канале {chat.username or chat.id}. Он больше не может оставлять комментарии под постами.')
            except Exception as ex:
                logger.error(traceback.format_exc())
        elif not chat.broadcast and chat.megagroup:
            session = await db.get_client(self.session_id)
            if not session.is_reacting:
                return
            # комментарий
            try:
                channel = await client(functions.channels.GetFullChannelRequest(chat))
                if channel and channel.full_chat and channel.full_chat.linked_chat_id and channel.full_chat.linked_chat_id in self.listening_channels:
                    try:
                        res = await client(functions.messages.SendReactionRequest(
                            peer=chat,
                            msg_id=event.message.id,
                            add_to_recent=True,
                            reaction=[types.ReactionEmoji(
                                emoticon='🔥'
                            )]
                        ))
                    except Exception:
                        # Reactions are limited in this chat
                        pass
            except Exception as ex:
                logger.error(traceback.format_exc())

    async def communication(self, event):
        db_client: TgClient = await db.get_client(self.session_id)
        if event.message.peer_id.channel_id == 2078563772:
            if event.message.reply_to:
                comments_list = await self.get_replied_comments_to_post(event, event.message)
                if not comments_list:
                    print('не нам')
                    return
                comments_list = comments_list[::-1]
                comments_list = list(map(lambda x: x.message, comments_list))
                next_phrase = gpt.get_dialog_phrase(comments_list, db_client.role)
                print(next_phrase)
                await self.client.send_message(event.chat, next_phrase, reply_to=event.message)

    async def get_replied_comments_to_post(self, event, last_msg: types.Message) -> list[types.Message] | bool:
        lst = [last_msg]
        msg = last_msg
        first_iter = True
        me = await self.client.get_entity('me')
        while msg.reply_to is not None:
            next_messages = (await self.client.get_messages(event.chat, ids=[msg.reply_to.reply_to_msg_id]))
            next_message: types.Message = next_messages[0]
            if first_iter and isinstance(next_message.from_id, types.PeerUser) and next_message.from_id.user_id != me.id:
                return False
            lst.append(next_message)
            msg = next_message
            first_iter = False
        return lst


# Message(id=941, peer_id=PeerChannel(channel_id=2078563772),
#         date=datetime.datetime(2024, 1, 18, 10, 1, 29, tzinfo=datetime.timezone.utc), message='да, отлично', out=False,
#         mentioned=True, media_unread=True, silent=False, post=False, from_scheduled=False, legacy=False,
#         edit_hide=False, pinned=False, noforwards=False, invert_media=False, from_id=PeerUser(user_id=901977201),
#         fwd_from=None, via_bot_id=None,
#         reply_to=MessageReplyHeader(reply_to_scheduled=False, forum_topic=False, quote=False, reply_to_msg_id=940,
#                                     reply_to_peer_id=None, reply_from=None, reply_media=None, reply_to_top_id=939,
#                                     quote_text=None, quote_entities=[], quote_offset=None), media=None,
#         reply_markup=None, entities=[], views=None, forwards=None, replies=None, edit_date=None, post_author=None,
#         grouped_id=None, reactions=None, restriction_reason=[], ttl_period=None)
