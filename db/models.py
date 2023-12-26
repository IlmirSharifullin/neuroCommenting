import asyncio
from enum import Enum

from sqlalchemy import String, Integer, Column, Table, ForeignKey, UniqueConstraint, SmallInteger, Boolean
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship


class ClientStatusEnum(Enum):
    RUNNING = 4
    JOINING = 3
    NOT_RUNNING = 2
    REPLACEABLE = 1
    BANNED = 0


class ChannelStatusEnum(Enum):
    OK = 1
    PRIVATE = 2


class UserStatusEnum(Enum):
    OK = 1
    BANNED = 2


class Base(DeclarativeBase):
    pass


listen_table = Table(
    'client_listen_table',
    Base.metadata,
    Column('client_id', Integer, ForeignKey('client.id', ondelete='CASCADE')),
    Column('channel_meta', String(255)),
    UniqueConstraint('client_id', 'channel_meta', name='listen_client')
)


class TgChannel(Base):
    __tablename__ = 'channel'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True)
    invite_hash = Column(String(255), nullable=True)
    chat_id = Column(Integer(), unique=True)
    status = Column(Integer(), default=1, nullable=False)

    def __str__(self):
        return f'Channel <{self.username}, {self.chat_id}>'


class TgClient(Base):
    __tablename__ = 'client'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True)
    status = Column(Integer(), default=1, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    about = Column(String())
    role = Column(String(), nullable=True)
    proxy = Column(String(255), nullable=True)
    min_answer_time = Column(Integer(), default=30)
    max_answer_time = Column(Integer(), default=300)
    is_premium = Column(Boolean(), default=False)
    send_as = Column(String(255), nullable=True)
    owner_id = Column(Integer, ForeignKey('user.chat_id'), nullable=True)
    owner = relationship('User', back_populates='sessions')

    def __str__(self):
        return f'Client <{self.session_id}, {self.status}>'


class User(Base):
    __tablename__ = 'user'

    chat_id = Column(Integer, primary_key=True)
    status = Column(Integer, nullable=False, default=UserStatusEnum.OK.value)
    sessions = relationship('TgClient', back_populates='owner')
