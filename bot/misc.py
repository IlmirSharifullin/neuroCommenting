from enum import IntEnum

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State

from db.models import TgClient
import db.funcs as db


class EditAction(IntEnum):
    FIRST_NAME = 0
    LAST_NAME = 1
    ABOUT = 2
    ROLE = 3
    PHOTO = 4
    ANSWER_TIME = 5


class SessionsCallback(CallbackData, prefix='getsession'):
    page: int
    session_id: str


class TurnSessionsPageCallback(CallbackData, prefix='turning'):
    page: int


class EditSessionCallback(CallbackData, prefix='editsession'):
    action: EditAction
    session_id: str


class EditSessionState(StatesGroup):
    val = State()


async def get_session_info(session_id):
    session: TgClient = await db.get_client(session_id)
    text = f'''
@{session.username}
Имя: {session.first_name or ''}
Фамилия: {session.last_name or ''}
Био: {session.about or ''}
Роль: {session.role or ''}
'''
    return text
