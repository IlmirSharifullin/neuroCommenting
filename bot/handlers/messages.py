import datetime
import os

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

import db.funcs as db
from bot.config import BOT_TOKEN, ADMIN_LIST
from bot.misc import EditSessionState, get_session_info
from client import Client
from db.models import *
from bot.keyboards import *

router = Router(name='messages-router')


@router.message((F.text == 'Сессии') & (F.from_user.id in ADMIN_LIST))
async def sessions_list_cmd(message: types.Message, page=1, from_callback=False):
    msg = []
    sessions = await db.get_clients()
    clients = []
    for client in sessions:
        line = f'@{client.username} {client.first_name} {client.last_name}'
        msg.append(line)
        clients.append(client)
    kb = get_sessions_keyboard(clients, page=page)

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
    db_client = await db.get_client(session_id)
    proxy = 0
    if field == EditAction.FIRST_NAME:
        session = Client(session_id, 0, [])
        await session.start()
        await session.update_profile(fname=value)
        await session.disconnect()
        await db.update_data(session_id, first_name=value)
    elif field == EditAction.LAST_NAME:
        session = Client(session_id, 0, [])
        await session.start()
        await session.update_profile(lname=value)
        await session.disconnect()
        await db.update_data(session_id, last_name=value)
    elif field == EditAction.ABOUT:
        session = Client(session_id, 0, [])
        await session.start()
        await session.update_profile(about=value)
        await session.disconnect()
        await db.update_data(session_id, about=value)
    elif field == EditAction.ROLE:
        await db.update_data(session_id, role=value)
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
    await message.answer(text=await get_session_info(session_id), reply_markup=get_session_edit_keyboard(session_id))
    await message.answer('Смена произошла успешно!')


@router.message(EditSessionState.val, F.content_type == 'photo')
async def edit_state_cmd(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data['field']
    session_id = data['session_id']
    if field == EditAction.PHOTO:
        value = message.text
        db_client = await db.get_client(session_id)
        print(message.photo)
        photo_file_id = message.photo[-1].file_id

        file_info = await message.bot.get_file(photo_file_id)
        print(file_info)
        filename = f'tempprofilephoto{datetime.datetime.now()}.jpg'
        await message.bot.download_file(file_info.file_path, f'data/images/{filename}')

        session = Client(session_id, 0, [])
        await session.start()
        await session.update_profile(photo_path=filename)
        os.remove(f'data/images/{filename}')
        await session.disconnect()
        await message.answer('Готово!')
    else:
        await message.answer('Ошибка. Попробуйте еще раз')


@router.message()
async def all_messages_cmd(message: types.Message):
    await message.answer('Не слушаю')
