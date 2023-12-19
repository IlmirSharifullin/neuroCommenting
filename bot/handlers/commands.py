from aiogram import Router, types, F
from aiogram.filters import Command

from db.models import *
from bot.keyboards import *

router = Router(name='commands-router')


@router.message(Command('start'), F.from_user.id.in_([901977201]))
async def start_cmd(message: types.Message):
    await message.answer('Главное меню ', reply_markup=types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text='Сессии')]], resize_keyboard=True))
