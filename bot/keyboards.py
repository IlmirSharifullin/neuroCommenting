import math
from enum import Enum, IntEnum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

import db.funcs as db
from bot.misc import SessionsCallback, TurnSessionsPageCallback, EditSessionCallback, EditAction, \
    StartStopSessionCallback, UpdateSessionCallback, BackToListCallback, BackToMenuCallback


def get_icon_by_status(status):
    if status == db.ClientStatusEnum.RUNNING:
        icon = '🟢'
    elif status == db.ClientStatusEnum.NOT_RUNNING:
        icon = '⏸'
    elif status == db.ClientStatusEnum.JOINING:
        icon = '⌛️'
    elif status == db.ClientStatusEnum.BANNED:
        icon = '❌'
    else:
        icon = ''
    return icon


def get_main_keyboard():
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Сессии'), KeyboardButton(text='Купить сессии')],
                                       [KeyboardButton(text='Поддежка'), KeyboardButton(text='Инфо', web_app=WebAppInfo(
                                           url='https://telegra.ph/INFO-dlya-polzovaniya-nejrokommentingom-01-11'))]],
                             resize_keyboard=True)
    return kb


def get_main_admin_keyboard():
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Сессии'), KeyboardButton(text='Купить сессии'), ],
                                       [KeyboardButton(text='Поддержка'), KeyboardButton(text='Инфо')],
                                       [KeyboardButton(text='Добавить сессии')]],
                             resize_keyboard=True)
    return kb


def get_sessions_keyboard(clients, page=1):
    count_on_page = 8
    pages_count = math.ceil(len(clients) / count_on_page)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for i in range((page - 1) * count_on_page, min(page * count_on_page, len(clients)), 2):
        status = db.ClientStatusEnum(clients[i].status)
        icon = get_icon_by_status(status)
        b1 = InlineKeyboardButton(
            text=f"{i + 1}. {clients[i].first_name} {icon}",
            callback_data=SessionsCallback(page=page, session_id=clients[i].session_id).pack())
        if i + 1 < len(clients):
            status = db.ClientStatusEnum(clients[i + 1].status)
            icon = get_icon_by_status(status)
            b2 = InlineKeyboardButton(
                text=f"{i + 2}. {clients[i + 1].first_name} {icon}",
                callback_data=SessionsCallback(page=page, session_id=clients[i + 1].session_id).pack())
        else:
            b2 = InlineKeyboardButton(text='', callback_data='null')
        keyboard.inline_keyboard.append([b1, b2])
    left_button = InlineKeyboardButton(text=f"◀️",
                                       callback_data=TurnSessionsPageCallback(
                                           page=pages_count if page == 1 else page - 1).pack())
    right_button = InlineKeyboardButton(text=f"▶️",
                                        callback_data=TurnSessionsPageCallback(
                                            page=1 if page == pages_count else page + 1).pack())
    back_button = InlineKeyboardButton(text=f'Назад', callback_data='backtomenu')
    keyboard.inline_keyboard.append([left_button, back_button, right_button])
    return keyboard


def get_session_edit_keyboard(session_id: str, session, page: int = 1):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    kb.inline_keyboard = [
        [InlineKeyboardButton(text='Запустить клиент',
                              callback_data=StartStopSessionCallback(action='start', session_id=session_id).pack()),
         InlineKeyboardButton(text='Остановить клиент',
                              callback_data=StartStopSessionCallback(action='stop', session_id=session_id).pack())
         ],
        [InlineKeyboardButton(text='Изменить имя',
                              callback_data=EditSessionCallback(action=EditAction.FIRST_NAME,
                                                                session_id=session_id).pack()),
         InlineKeyboardButton(text='Изменить фамилию',
                              callback_data=EditSessionCallback(action=EditAction.LAST_NAME,
                                                                session_id=session_id).pack()),
         InlineKeyboardButton(text='Изменить био',
                              callback_data=EditSessionCallback(action=EditAction.ABOUT,
                                                                session_id=session_id).pack())
         ],
        [InlineKeyboardButton(text='Изменить роль',
                              callback_data=EditSessionCallback(action=EditAction.ROLE,
                                                                session_id=session_id).pack()),
         InlineKeyboardButton(text='Изменить фото',
                              callback_data=EditSessionCallback(action=EditAction.PHOTO,
                                                                session_id=session_id).pack())
         ],
        [InlineKeyboardButton(text='Изменить прокси',
                              callback_data=EditSessionCallback(action=EditAction.PROXY, session_id=session_id).pack()),
         InlineKeyboardButton(text='Изменить список каналов',
                              callback_data=EditSessionCallback(action=EditAction.LISTEN_CHANNELS,
                                                                session_id=session_id).pack())
         ],
        [InlineKeyboardButton(text='Изменить лицо отправки',
                              callback_data=EditSessionCallback(action=EditAction.SEND_AS,
                                                                session_id=session_id).pack()),
         InlineKeyboardButton(text='Изменить имя пользователя',
                              callback_data=EditSessionCallback(action=EditAction.USERNAME,
                                                                session_id=session_id).pack()),
         ],
        [InlineKeyboardButton(text='Ответ на пост', callback_data=EditSessionCallback(action=EditAction.ANSWER_POSTS,
                                                                                      session_id=session_id).pack()),
         InlineKeyboardButton(text='Изменить время комментирования',
                              callback_data=EditSessionCallback(action=EditAction.ANSWER_TIME,
                                                                session_id=session_id).pack()),
         ],
        [
            InlineKeyboardButton(
                text='Выключить реакции на комментарии' if session.is_reacting else 'Включить реакции на комментарии',
                callback_data=EditSessionCallback(action=EditAction.IS_REACTING,
                                                  session_id=session_id).pack()),
            InlineKeyboardButton(
                text='Выключить нейросеть' if session.is_neuro else 'Включить нейросеть',
                callback_data=EditSessionCallback(action=EditAction.IS_NEURO_OFF if session.is_neuro else EditAction.IS_NEURO_ON,
                                                  session_id=session_id).pack())
        ],
        [InlineKeyboardButton(text='Обновить сессию',
                              callback_data=UpdateSessionCallback(session_id=session_id, page=page).pack()),
         InlineKeyboardButton(text='Назад', callback_data=BackToListCallback(page=page).pack())
         ]
    ]
    return kb
