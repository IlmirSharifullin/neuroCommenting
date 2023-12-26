from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, InputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import user_running_sessions
from bot.handlers.messages import sessions_list_cmd
from bot.misc import EditSessionState, get_session_info, BuySessionState
from client import Client
from db.models import *
from bot.keyboards import *

router = Router(name='callbacks-router')


@router.callback_query(SessionsCallback.filter())
async def session_cmd(query: CallbackQuery, callback_data: SessionsCallback):
    await query.answer()

    kb = get_session_edit_keyboard(callback_data.session_id)
    await query.message.answer(text=await get_session_info(callback_data.session_id), reply_markup=kb, parse_mode='html')


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
        await query.message.answer('Приложите новое фото (не файлом)')
    elif callback_data.action == EditAction.ANSWER_TIME:
        await query.message.answer(
            'Введите время ожидания перед отправкой коммента в формате <МИН>-<МАКС>. Ждет случайное кол-во секунд в этом промежутке, после чего отправит комментарий')
    elif callback_data.action == EditAction.PROXY:
        await query.message.answer('Введите новый прокси в формате {login}:{password}@{ip}:{port}. Поддерживаемый протокол - <b>SOCKS5!</b>', parse_mode='html')
    elif callback_data.action == EditAction.LISTEN_CHANNELS:
        await query.message.answer('Приложите .txt файл, в котором каждое с новой строки перечислены юзернеймы каналов без "@" (или их invite hash в формате "+XXXXXX". \nПример: Ссылка для присоединения - t.me/+ABCDEF, invite_hash - "+ABCDEF").')
    elif callback_data.action == EditAction.SEND_AS:
        session = await db.get_client(callback_data.session_id)
        if session.is_premium:
            await query.message.answer('Введите юзернейм канала для отправки от его лица.\nВАЖНО!!! Для этого сессия должна быть владельцем этого канала.')
        else:
            await query.message.answer('Для настройки отправки от лица канала, нужно чтобы сессия обладала премиум аккаунтом. Вы можете подарить ему премиум.')
            await state.clear()
    elif callback_data.action == EditAction.USERNAME:
        await query.message.answer('Введите новый юзернейм для сессии')
    else:
        await state.clear()
        await query.message.answer('Пока не работает')


@router.callback_query(StartStopSessionCallback.filter(F.action == 'start'))
async def start_session(query: CallbackQuery, callback_data: StartStopSessionCallback):
    running_sessions = user_running_sessions.get(query.from_user.id, [])
    running_sessions_ids = [i.session_id for i in running_sessions]

    session_id = callback_data.session_id

    if session_id in running_sessions_ids:
        await query.message.answer('Клиент уже запущен')
        return False

    client = Client(session_id)
    await client.init_session()

    running_sessions.append(client)
    user_running_sessions[query.from_user.id] = running_sessions

    asyncio.create_task(client.run())
    await query.message.answer('Клиент успешно включен. Подписывается на нужные каналы')
    await query.answer()


@router.callback_query(StartStopSessionCallback.filter(F.action == 'stop'))
async def start_session(query: CallbackQuery, callback_data: StartStopSessionCallback):
    running_sessions = user_running_sessions.get(query.from_user.id, [])

    session_id = callback_data.session_id

    client = None
    for cli in running_sessions:
        if cli.session_id == session_id:
            client = cli

    if client is None:
        await query.message.answer('Клиент не запущен на данный момент')
    else:
        await client.disconnect()
        running_sessions.remove(client)
        user_running_sessions[query.from_user.id] = running_sessions
        await query.message.answer('Клиент отключен')
    await query.answer()


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


@router.callback_query(UpdateSessionCallback.filter())
async def update_session(query: CallbackQuery, callback_data: UpdateSessionCallback):
    session_id = callback_data.session_id
    client = Client(session_id)
    await client.init_session()
    await client.start()
    me = await client.client.get_me()
    await db.update_data(session_id, username=me.username, first_name=me.first_name, last_name=me.last_name, is_premium=me.premium)
    await client.disconnect()
    await query.answer('Сессия обновлена!')


@router.callback_query()
async def not_handled(query: CallbackQuery):
    print(query.data.__class__)
    print('not handled')
