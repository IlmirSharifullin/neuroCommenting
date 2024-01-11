import datetime
import os
import re

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from telethon import functions, errors

from bot.config import ADMIN_LIST
from bot.misc import EditSessionState, get_session_info
from client import Client, ProxyNotFoundError
from bot.keyboards import *
from proxies.proxy import Proxy

router = Router(name='messages-router')


@router.message(F.text == 'Поддержка')
async def support_cmd(message: types.Message):
    await message.answer('При появлении вопросов пишите @zamaneurosupport')


@router.message((F.text == 'Сессии') & (F.from_user.id in ADMIN_LIST))
async def sessions_list_cmd(message: types.Message, page=1, from_callback=False):
    msg = []
    sessions = await db.get_clients_by_owner_id(message.chat.id)
    for client in sessions:
        line = f'@{client.username} {client.first_name} {client.last_name}'
        msg.append(line)

    kb = get_sessions_keyboard(sessions, page=page)

    if from_callback:
        await message.edit_text('\n'.join(msg), parse_mode='', reply_markup=kb)
    else:
        await message.answer('\n'.join(msg), parse_mode='', reply_markup=kb)


@router.message(EditSessionState.val, F.text == 'Отмена')
async def cancel_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    session_id = data['session_id']

    session = await db.get_client(session_id)
    await state.clear()
    await message.answer(text=await get_session_info(session_id),
                         reply_markup=get_session_edit_keyboard(session_id, is_reacting=session.is_reacting),
                         parse_mode='html')


@router.message(EditSessionState.val, F.content_type == 'text')
async def edit_state_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data['field']
    session_id = data['session_id']
    value = message.text
    try:

        if field == EditAction.FIRST_NAME:
            session = Client(session_id, changing=True)
            await session.init_session()
            await session.start()
            await session.update_profile(fname=value)
            await session.disconnect()
            await db.update_data(session_id, first_name=value)
        elif field == EditAction.LAST_NAME:
            session = Client(session_id, changing=True)
            await session.init_session()
            await session.start()
            await session.update_profile(lname=value)
            await session.disconnect()
            await db.update_data(session_id, last_name=value)
        elif field == EditAction.ABOUT:
            session = Client(session_id, changing=True)
            await session.init_session()
            await session.start()
            await session.update_profile(about=value)
            await session.disconnect()
            await db.update_data(session_id, about=value)
        elif field == EditAction.ROLE:
            await db.update_data(session_id, role=value)
        elif field == EditAction.PROXY:
            if Proxy.validate_proxy_format(value):
                await db.update_data(session_id, proxy=value)
            else:
                await message.answer('Неверный формат прокси. Попробуйте еще раз..')
                return
        elif field == EditAction.ANSWER_TIME:
            try:
                mini, maxi = value.split('-')
                mini, maxi = int(mini), int(maxi)
                if mini > maxi:
                    raise ValueError
                await db.update_data(session_id, min_answer_time=mini, max_answer_time=maxi)
            except ValueError:
                return await message.answer('Неверный формат ввода. Попробуйте еще раз..')
        elif field == EditAction.SEND_AS:
            session = Client(session_id, changing=True)
            await session.init_session()
            await session.start()
            try:
                await session.client(functions.messages.SaveDefaultSendAsRequest('BotTalk', value))
            except errors.PeerIdInvalidError | errors.SendAsPeerInvalidError:
                await session.disconnect()
                return await message.answer('Ошибка..')
            else:
                await db.update_data(session_id, send_as=value)
            await session.disconnect()
        elif field == EditAction.USERNAME:
            if not re.match(r"[a-zA-Z][\w\d]{3,30}[a-zA-Z\d]", value):
                return await message.answer('Неправильный юзернейм. Попробуйте еще раз..')

            session = Client(session_id, changing=True)
            await session.init_session()
            await session.start()
            try:
                await session.client(functions.account.UpdateUsernameRequest(value))
            except errors.UsernameInvalidError:
                return await message.answer('Неправильный юзернейм. Попробуйте еще раз..')
            except errors.UsernameNotModifiedError:
                return await message.answer('Юзернейм не изменился')
            except errors.UsernameOccupiedError:
                return await message.answer('Юзернейм занят')
            else:
                await message.answer('Юзернейм успешно изменён')
            await db.update_data(session_id, username=value)
            await session.disconnect()
        elif field == EditAction.ANSWER_POSTS:
            if value.isdigit():
                value = int(value)
                await db.update_data(session_id, answer_posts=value)
            else:
                return await message.answer('Нужно ввести число')
        else:
            return await message.answer('Ошибка. Попробуйте еще раз')

        await state.clear()
        session = await db.get_client(session_id)
        await message.answer(text=await get_session_info(session_id),
                             reply_markup=get_session_edit_keyboard(session_id, is_reacting=session.is_reacting),
                             parse_mode='html')
        await message.answer('Смена произошла успешно!')
    except ProxyNotFoundError:
        await message.answer(
            'Без прокси мы не можем присоединяться к сессии для изменения профиля. Добавьте прокси чтобы продолжить')


@router.message(EditSessionState.val, F.content_type == 'photo')
async def edit_state_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data['field']
    session_id = data['session_id']
    if field == EditAction.PHOTO:
        print(message.photo)
        photo_file_id = message.photo[-1].file_id

        file_info = await message.bot.get_file(photo_file_id)
        print(file_info)
        filename = f'tempprofilephoto{datetime.datetime.now()}.jpg'
        await message.bot.download_file(file_info.file_path, f'data/images/{filename}')

        session = Client(session_id, changing=True)
        try:
            await session.init_session()
        except ProxyNotFoundError:
            return await message.answer(
                'У клиента нет прокси. Без прокси мы не можем подключиться к сессии для изменения профиля')
        await session.start()
        await session.update_profile(photo_path=filename)
        os.remove(f'data/images/{filename}')
        await session.disconnect()
        await message.answer('Готово!')

        await state.clear()
    else:
        await message.answer('Ошибка. Попробуйте еще раз..')


@router.message(EditSessionState.val, F.content_type == 'document')
async def get_listen_channels_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    session_id = data['session_id']
    field = data['field']
    if field == EditAction.LISTEN_CHANNELS:
        file_id = message.document.file_id
        file_format = message.document.mime_type
        if file_format == 'text/plain':
            file_info = await message.bot.get_file(file_id)
            filename = f'temp{datetime.datetime.now()}'
            await message.bot.download_file(file_info.file_path, f'data/{filename}')
            with open(f'data/{filename}') as f:
                channels_meta = f.read().strip().split('\n')
            os.remove(f'data/{filename}')
            client = await db.get_client(session_id)
            await db.update_listening_channels(client.id, channels_meta)

            await state.clear()

            session = await db.get_client(session_id)
            await message.answer(text=await get_session_info(session_id),
                                 reply_markup=get_session_edit_keyboard(session_id, is_reacting=session.is_reacting),
                                 parse_mode='html')
            await message.answer('Готово!')
        else:
            await message.answer('Неправильный формат')
    else:
        await message.answer('Ошибка. Попробуйте еще раз..')


@router.message()
async def all_messages_cmd(message: types.Message):
    await message.answer('Не слушаю')
