from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

import db.funcs as db
from bot.misc import BuySessionState

router = Router(name='buysessions-router')


@router.message(F.text == 'Купить сессии')
async def buy_sessions_cmd(message: Message, state: FSMContext):
    free_sessions_count = await db.get_free_sessions_count()
    await message.answer(
        f'Покупка доступна от 3-х сессий. На данный момент доступно {free_sessions_count} сессий.\nСтоимость - n рублей. Введите количество сессий к покупке.')
    await state.set_state(BuySessionState.count)


@router.message(BuySessionState.count)
async def buy_sessions_count_cmd(message: Message, state: FSMContext):
    count = message.text
    if not count.isdigit():
        return await message.answer('Введите число - количество сессий к покупке')

    count = int(count)
    if count < 3:
        return await message.answer('Количество сессий должно быть не менее 3-х')

    free_sessions_count = await db.get_free_sessions_count()
    if count > free_sessions_count:
        return await message.answer('Такое количество недоступно к покупке. Попробуйте в другой раз..')

    await message.answer('Отлично! Вот ссылка на оплату', reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Типо ссылка', callback_data='paid')]]))

    await state.set_data({'count': count})
    await state.set_state(BuySessionState.paying)


@router.callback_query(BuySessionState.paying, F.data == 'paid')
async def paid_cmd(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    count = data['count']
    sessions = await db.get_random_free_sessions(count)
    for session in sessions:
        print(session)
        await db.set_owner_to_session(session.session_id, query.from_user.id)

    await query.answer()
    await query.message.answer('Оплата прошла успешно! Ваши новые сессии появились в списке')
    await state.clear()
