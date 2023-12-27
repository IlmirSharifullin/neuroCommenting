from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from bot.config import ADMIN_LIST
from db.models import *
from bot.keyboards import *

router = Router(name='commands-router')


@router.message(Command('start'), F.from_user.id.in_(ADMIN_LIST))
async def start_cmd(message: types.Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        user: User = await db.insert_user(message.from_user.id)
    if len(await db.get_users_sessions(user.chat_id)) == 0:
        pass

    data = get_main_menu(message.from_user.id)
    await message.answer(data['text'], reply_markup=data['reply_markup'])


def get_main_menu(uid: int):
    if uid in ADMIN_LIST:
        kb = get_main_admin_keyboard()
    else:
        kb = get_main_keyboard()

    return {'text': 'Главное меню', 'reply_markup': kb}
