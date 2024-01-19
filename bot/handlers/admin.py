import datetime
import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import ADMIN_LIST
from bot.misc import AddSessionsState
from utils.add_sesssions_by_zip import read_archive_sessions, add_temp_sessions

router = Router(name='admin-router')


@router.message(F.from_user.id.in_(ADMIN_LIST), F.text == 'Добавить сессии')
async def add_sessions_cmd(message: Message, state: FSMContext):
    await message.answer('Приложите .zip архив с папками session+json сессий в нём')
    await state.set_state(AddSessionsState.archive)


@router.message(AddSessionsState.archive, F.document, F.from_user.id.in_(ADMIN_LIST))
async def add_archive_sessions(message: Message, state: FSMContext):
    file_id = message.document.file_id
    file_format = message.document.mime_type
    file_info = await message.bot.get_file(file_id)
    filename = f'temp{datetime.datetime.now()}'
    await message.bot.download_file(file_info.file_path, f'data/{filename}')

    read_archive_sessions(f'data/{filename}')
    res = await add_temp_sessions()
    errors = '\n'.join(res['errors'])

    os.remove(f'data/{filename}')

    await state.clear()
    ans = f'''
Готово!
Старых сессий повторно: {res['old']}
Новых сессий добавлено: {res['new']}
Из новых сессий в бане: {res['banned']}
Лог ошибок: {errors}
'''
    await message.answer(ans)
