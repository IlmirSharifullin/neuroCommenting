import os

from aiogram import Router, F, types

import db.funcs as db
from db.models import *
from bot.keyboards import *

router = Router(name='messages-router')


@router.message((F.text == 'Сессии') & (F.from_user.id in [901977201]))
async def sessions_list_cmd(message: types.Message):
    sessions = os.listdir('../sessions')
    print(sessions)
    msg = []
    for session_id in sessions:
        client: TgClient = await db.get_client(session_id)
        line = f'@{client.username} {client.first_name} {client.last_name}'
        msg.append(line)
    await message.answer('\n'.join(msg), parse_mode='')


@router.message()
async def all_messages_cmd(message: types.Message):
    await message.answer('Не слушаю')
