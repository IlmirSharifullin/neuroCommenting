import traceback

import asyncio
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from config import async_session_maker
from db.models import TgChannel, TgClient, ClientStatusEnum, User, UserStatusEnum, listen_table

from functools import wraps
from typing import Callable, List, Optional


def with_session(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            async with async_session_maker() as session:
                result = await func(*args, session, **kwargs)
                await session.commit()
            return result
        except Exception as ex:
            print(traceback.format_exc())

    return wrapper


@with_session
async def get_channels(session: AsyncSession) -> List[TgChannel]:
    query = await session.execute(select(TgChannel).order_by(TgChannel.id))
    channels = list(query.scalars())
    return channels


@with_session
async def get_channel(data: str | int, session: AsyncSession):
    if isinstance(data, int):
        query = await session.execute(select(TgChannel).where(TgChannel.chat_id == data))
    else:
        query = await session.execute(
            select(TgChannel).where((TgChannel.username == data) | (TgChannel.invite_hash == data)))
    res = query.scalar()
    return res


@with_session
async def get_channel_by_id(id: int, session: AsyncSession):
    query = await session.execute(select(TgChannel).filter_by(id=id))
    res = query.scalar()
    return res


@with_session
async def get_client(session_id: str, session: AsyncSession) -> TgClient:
    query = await session.execute(select(TgClient).where(TgClient.session_id == session_id))
    return query.scalar()


@with_session
async def get_clients(session: AsyncSession) -> List[TgClient]:
    query = await session.execute(select(TgClient).where(TgClient.status != ClientStatusEnum.BANNED.value))
    channels = list(query.scalars())
    return channels


@with_session
async def insert_channel(chat_id: int, username: str, session: AsyncSession) -> Optional[TgChannel]:
    try:
        channel = await session.execute(
            insert(TgChannel).values(chat_id=chat_id, username=username).returning(TgChannel))
        return channel.scalar()
    except Exception as ex:
        channel = await get_channel(chat_id)
        return channel


@with_session
async def insert_client(session_id: str, session: AsyncSession, status=ClientStatusEnum.REPLACEABLE.value) -> Optional[
    TgClient]:
    try:
        client = await session.execute(
            insert(TgClient).values(session_id=session_id, status=status).returning(TgClient))
        client = client.scalar()
        await session.commit()
        return client
    except Exception as ex:
        print(ex)
        return None


@with_session
async def set_status(session_id: str, status: ClientStatusEnum, session: AsyncSession):
    cli: TgClient = await get_client(session_id)

    if cli is None:
        await insert_client(session_id, status=status.value)
    else:
        await session.execute(update(TgClient)
                              .values(status=status.value)
                              .filter_by(session_id=session_id))
        await session.commit()


@with_session
async def get_listening_channels(client_id: int, session: AsyncSession):
    query = await session.execute(select(listen_table).filter_by(client_id=client_id))
    channels_meta = [i[1] for i in list(query.fetchall())]
    return channels_meta


@with_session
async def update_listening_channels(session_id: str, channels_meta: List[str], session: AsyncSession):
    query = await session.execute(delete(listen_table).filter_by(client_id=session_id))
    await session.commit()
    for channel_meta in channels_meta:
        query = await session.execute(
            insert(listen_table).values(client_id=session_id, channel_meta=channel_meta))


@with_session
async def update_data(session_id: str, session: AsyncSession, first_name: str = None, last_name: str = None,
                      about: str = None, role: str = None, proxy: str = None,
                      username: str = None, min_answer_time: int = None, max_answer_time: int = None):
    client: TgClient = await get_client(session_id)
    await session.execute(
        update(TgClient).filter_by(session_id=session_id).values(first_name=first_name or client.first_name,
                                                                 last_name=last_name or client.last_name,
                                                                 about=about or client.about,
                                                                 role=role or client.role,
                                                                 username=username or client.username,
                                                                 proxy=proxy or client.proxy,
                                                                 min_answer_time=min_answer_time or client.min_answer_time,
                                                                 max_answer_time=max_answer_time or client.max_answer_time))

    return await session.commit()


@with_session
async def get_random_free_session(session: AsyncSession):
    query = await session.execute(select(TgClient).filter_by(status=ClientStatusEnum.REPLACEABLE.value).limit(1))
    client = query.scalar()
    if client:
        return client.session_id
    else:
        return None


@with_session
async def get_clients_by_owner_id(chat_id: int, session: AsyncSession):
    query = await session.execute(select(TgClient).filter_by(owner_id=chat_id))
    res = list(query.scalars())
    return res


@with_session
async def get_user(chat_id: int, session: AsyncSession):
    query = await session.execute(select(User).filter_by(chat_id=chat_id))
    user: User = query.scalar()
    return user


@with_session
async def insert_user(chat_id: int, session: AsyncSession):
    query = await session.execute(insert(User).values(chat_id=chat_id, status=UserStatusEnum.OK.value).returning(User))
    user = query.scalar()
    await session.commit()
    return user


@with_session
async def get_users_sessions(chat_id: int, session: AsyncSession):
    query = await session.execute(select(TgClient).filter_by(owner_id=chat_id))
    res = list(query.scalars())
    return res


async def test():
    print(await get_channel('bugulma'))
