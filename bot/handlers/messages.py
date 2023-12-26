import datetime
import os

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

import db.funcs as db
from bot.config import BOT_TOKEN, ADMIN_LIST
from bot.misc import EditSessionState, get_session_info, BuySessionState
from client import Client, ProxyNotFoundError
from db.models import *
from bot.keyboards import *
from proxies.proxy import Proxy

router = Router(name='messages-router')


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


@router.message(EditSessionState.val, F.content_type == 'text')
async def edit_state_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data['field']
    session_id = data['session_id']
    value = message.text

    if field == EditAction.FIRST_NAME:
        session = Client(session_id)
        await session.init_session()
        await session.start()
        await session.update_profile(fname=value)
        await session.disconnect()
        await db.update_data(session_id, first_name=value)
    elif field == EditAction.LAST_NAME:
        session = Client(session_id)
        await session.init_session()
        await session.start()
        await session.update_profile(lname=value)
        await session.disconnect()
        await db.update_data(session_id, last_name=value)
    elif field == EditAction.ABOUT:
        session = Client(session_id)
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
            await message.answer('Неверный формат ввода. Попробуйте еще раз..')
    else:
        return await message.answer('Ошибка. Попробуйте еще раз')

    await state.clear()

    await message.answer(text=await get_session_info(session_id), reply_markup=get_session_edit_keyboard(session_id), parse_mode='html')
    await message.answer('Смена произошла успешно!')


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

        session = Client(session_id, [])
        await session.init_session()
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

            await message.answer(text=await get_session_info(session_id),
                                 reply_markup=get_session_edit_keyboard(session_id), parse_mode='html')
            await message.answer('Готово!')
        else:
            await message.answer('Неправильный формат')
    else:
        await message.answer('Ошибка. Попробуйте еще раз..')


@router.message(F.text == 'Купить сессии')
async def buy_sessions_cmd(message: types.Message, state: FSMContext):
    free_sessions_count = await db.get_free_sessions_count()
    await message.answer(f'Покупка доступна от 3-х сессий. На данный момент доступно {free_sessions_count} сессий.\nСтоимость - n рублей. Введите количество сессий к покупке.')
    await state.set_state(BuySessionState.count)


@router.message(BuySessionState.count)
async def buy_sessions_count_cmd(message: types.Message, state: FSMContext):
    count = message.text
    if not count.isdigit():
        return await message.answer('Введите число - количество сессий к покупке')

    count = int(count)
    if count < 3:
        return await message.answer('Количество сессий должно быть не менее 3-х')

    free_sessions_count = await db.get_free_sessions_count()
    if count > free_sessions_count:
        return await message.answer('Такое количество недоступно к покупке. Попробуйте в другой раз..')

    await message.answer('Отлично! Вот ссылка на оплату', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Типо ссылка', callback_data='paid')]]))

    await state.set_data({'count': count})
    await state.set_state(BuySessionState.paying)


@router.message()
async def all_messages_cmd(message: types.Message):
    await message.answer('Не слушаю')