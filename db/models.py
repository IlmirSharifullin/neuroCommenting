from enum import Enum

from sqlalchemy import String, Integer, Column, Table, ForeignKey, UniqueConstraint, SmallInteger, Boolean
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship


class ClientStatusEnum(Enum):
    USING = 1
    BANNED = 2
    FREE = 3


class ChannelStatusEnum(Enum):
    OK = 1
    PRIVATE = 2


class SexEnum(Enum):
    MAN = 0
    WOMAN = 1


class Base(DeclarativeBase):
    pass


association_table = Table(
    'client_channel_association',
    Base.metadata,
    Column('client_id', Integer, ForeignKey('client.id', ondelete='CASCADE')),
    Column('channel_id', Integer, ForeignKey('channel.id', ondelete='CASCADE')),
    UniqueConstraint('client_id', 'channel_id', name='uq_client_channel')

)


class TgChannel(Base):
    __tablename__ = 'channel'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True)
    chat_id = Column(Integer(), unique=True)
    status = Column(Integer(), default=1, nullable=False)
    joined_clients = relationship('TgClient', secondary=association_table, back_populates='joined_channels')

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
    sex = Column(SmallInteger(), default=0)
    photo_path = Column(String(255))
    role = Column(String(), nullable=True)
    joined_channels = relationship('TgChannel', secondary=association_table, back_populates='joined_clients')

    def __str__(self):
        return f'Client <{self.session_id}, {self.status}>'
