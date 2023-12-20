from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, InputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.messages import sessions_list_cmd
from bot.misc import EditSessionState, get_session_info
from db.models import *
from bot.keyboards import *

router = Router(name='callbacks-router')


@router.callback_query(SessionsCallback.filter())
async def session_cmd(query: CallbackQuery, callback_data: SessionsCallback):
    await query.answer()

    kb = get_session_edit_keyboard(callback_data.session_id)
    await query.message.answer(text=await get_session_info(callback_data.session_id), reply_markup=kb)


@router.callback_query(TurnSessionsPageCallback.filter())
async def turn_sessions_page_cmd(query: CallbackQuery, callback_data: TurnSessionsPageCallback):
    await sessions_list_cmd(query.message, page=callback_data.page, from_callback=True)


@router.callback_query(EditSessionCallback.filter())
async def edit_session(query: CallbackQuery, callback_data: EditSessionCallback, state: FSMContext):
    await state.set_state(EditSessionState.val)
    await state.update_data(field=callback_data.action, session_id=callback_data.session_id)
    if callback_data.action == EditAction.FIRST_NAME:
        await query.message.answer('Введите новое имя клиента')
    elif callback_data.action == EditAction.LAST_NAME:
        await query.message.answer('Введите новую фамилию клиента')
    elif callback_data.action == EditAction.ABOUT:
        await query.message.answer('Введите новую биографию клиента')
    elif callback_data.action == EditAction.ROLE:
        await query.message.answer('Введите новую роль клиента')
    elif callback_data.action == EditAction.PHOTO:
        await query.message.answer('Скиньте новое фото (не файлом)')
    elif callback_data.action == EditAction.ANSWER_TIME:
        await query.message.answer(
            'Введите время ожидания перед отправкой коммента в формате <МИН>-<МАКС>. Ждет случайное кол-во секунд в этом промежутке, после чего отправит комментарий')


@router.callback_query()
async def not_handled(query: CallbackQuery):
    print(query.data.__class__)
    print('not handled')
