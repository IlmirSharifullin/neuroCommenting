from enum import IntEnum

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State

from db.models import TgClient, ClientStatusEnum
import db.funcs as db


class EditAction(IntEnum):
    FIRST_NAME = 0
    LAST_NAME = 1
    ABOUT = 2
    ROLE = 3
    PHOTO = 4
    ANSWER_TIME = 5
    PROXY = 6
    LISTEN_CHANNELS = 7
    SEND_AS = 8
    USERNAME = 9
    ANSWER_POSTS = 10
    IS_REACTING = 11
    IS_NEURO_ON = 12
    IS_NEURO_OFF = 13

class SessionsCallback(CallbackData, prefix='getsession'):
    page: int
    session_id: str


class TurnSessionsPageCallback(CallbackData, prefix='turning'):
    page: int


class EditSessionCallback(CallbackData, prefix='editsession'):
    action: EditAction
    session_id: str


class UpdateSessionCallback(CallbackData, prefix='updatesession'):
    session_id: str
    page: int


class StartStopSessionCallback(CallbackData, prefix='startstopsession'):
    action: str
    session_id: str


class BackToListCallback(CallbackData, prefix='backtolist'):
    page: int

class BackToMenuCallback(CallbackData, prefix='backtomenu'):
    pass


class EditSessionState(StatesGroup):
    val = State()


class BuySessionState(StatesGroup):
    count = State()
    paying = State()


class AddSessionsState(StatesGroup):
    archive = State()


class SetTextState(StatesGroup):
    text = State()


async def get_session_info(session_id):
    session: TgClient = await db.get_client(session_id)
    listening_channels = await db.get_listening_channels(session.id)
    text = f'''
@{session.username or ''}
Имя: {session.first_name or ''}
Фамилия: {session.last_name or ''}
Био: {session.about or ''}
Статус: {ClientStatusEnum.get_label(session.status)}
Премиум: {'Есть' if session.is_premium else 'Отсутствует'}
Ставит реакции на комментарии под постами: {'Да' if session.is_reacting else 'Нет'}
Отвечает от имени: {session.send_as if session.send_as and session.is_premium else 'Своего'}
Отвечает на пост прождав от {session.min_answer_time} до {session.max_answer_time} секунд
Отвечает на каждый {session.answer_posts}-й пост в канале
Прокси: {'<span class="tg-spoiler">' + session.proxy + '</span>' if session.proxy else 'Нет прокси. Без прокси клиент не будет запускаться'}
Режим: {'Нейросеть' if session.is_neuro else 'Готовый текст'}
{'Роль: ' + (session.role or '') if session.is_neuro else 'Текст: ' + (session.text or '')}
Список прослушиваемых каналов: '''
    for channel_meta in listening_channels:
        if channel_meta.startswith('+'):
            text += f't.me/{channel_meta}'
        else:
            text += f'@{channel_meta}'
        text += ', '
    text = text[:-2]
    return text
