import asyncio
import traceback

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from config import async_session_maker
from db.models import TgChannel, TgClient, ClientStatusEnum, association_table

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
async def get_channel(username: str, session: AsyncSession):
    query = await session.execute(select(TgChannel).where(TgChannel.username == username))
    return query.scalar()


@with_session
async def get_client(session_id: str, session: AsyncSession) -> TgClient:
    query = await session.execute(select(TgClient).where(TgClient.session_id == session_id))
    return query.scalar()


@with_session
async def insert_channel(chat_id: int, username: str, session: AsyncSession) -> Optional[TgChannel]:
    try:
        channel = await session.execute(insert(TgChannel).values(chat_id=chat_id, username=username))
        await session.commit()
        return channel.scalar()
    except Exception as ex:
        return None


@with_session
async def insert_client(session_id: str, session: AsyncSession, status=ClientStatusEnum.OK.value) -> Optional[TgClient]:
    try:
        client = await session.execute(insert(TgClient).values(session_id=session_id, status=status).returning(TgClient))
        client = client.scalar()
        await session.commit()
        return client
    except Exception as ex:
        print(ex)
        return None


@with_session
async def set_banned_status(session_id: str, session: AsyncSession):
    cli: TgClient = await get_client(session_id)

    if cli is None:
        await insert_client(session_id, status=ClientStatusEnum.BANNED.value)
    else:
        cli.status = ClientStatusEnum.BANNED.value
        await session.execute(
            update(TgClient).values(status=ClientStatusEnum.BANNED.value).filter_by(session_id=session_id))
        await session.commit()


@with_session
async def get_joined_clients(channel: TgChannel, session: AsyncSession):
    query = await session.execute(select(association_table).filter_by(channel_id=channel.id))
    return list(query.scalars())


@with_session
async def get_joined_channels(client: TgClient, session: AsyncSession):
    query = await session.execute(select(association_table).filter_by(client_id=client.id))
    return list(query.scalars())


@with_session
async def add_join(client: TgClient, channel: TgChannel, session: AsyncSession):
    await session.execute(insert(association_table).values(client_id=client.id, channel_id=channel.id))
    await session.commit()


@with_session
async def update_data(session_id: str, session: AsyncSession, first_name: str = None, last_name: str = None,
                      sex: int = None, photo_path: str = None, about: str = None):
    print('update db')
    client: TgClient = await get_client(session_id)
    await session.execute(
        update(TgClient).filter_by(session_id=session_id).values(first_name=first_name or client.first_name,
                                                                 last_name=last_name or client.last_name,
                                                                 sex=sex or client.sex,
                                                                 photo_path=photo_path or client.photo_path,
                                                                 about=about or client.about))

    return await session.commit()
