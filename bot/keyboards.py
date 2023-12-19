import math

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import db.funcs as db


def get_clients_keyboard(clients, page=1):
    count_on_page = 8
    pages_count = math.ceil(len(clients) / count_on_page)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for i in range((page - 1) * count_on_page, min(page * count_on_page, len(clients)), 2):
        b1 = InlineKeyboardButton(text=f"{i + 1}. {clients[i].first_name} {'🟢' if db.ClientStatusEnum(clients[i].status) == db.ClientStatusEnum.USING else '🆓'}",
                                  callback_data=f'clients_{clients[i].session_id}_{page}')
        if i + 1 < len(clients):
            b1 = InlineKeyboardButton(
                text=f"{i + 2}. {clients[i+1].first_name} {'🟢' if db.ClientStatusEnum(clients[i].status) == db.ClientStatusEnum.USING else '🆓'}",
                callback_data=f'clients_{clients[i+1].session_id}_{page}')
        else:
            b2 = InlineKeyboardButton(text='', callback_data='null')
        keyboard.inline_keyboard.append([b1, b2])
    left_button = InlineKeyboardButton(text=f"◀️", callback_data=f'clientspage_{pages_count if page == 1 else page - 1}')
    right_button = InlineKeyboardButton(text=f"▶️", callback_data=f'clientspage_{1 if page == pages_count else page + 1}')
    back_button = InlineKeyboardButton(text=f'Назад', callback_data=f'cancel')
    keyboard.inline_keyboard.append([left_button, back_button, right_button])
    return keyboard