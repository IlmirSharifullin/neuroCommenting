from enum import Enum

from sqlalchemy import String, Integer, Column, Table, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship


class ClientStatusEnum(Enum):
    RUNNING = 4
    JOINING = 3
    NOT_RUNNING = 2
    REPLACEABLE = 1
    BANNED = 0

    @classmethod
    def get_label(cls, status):
        if status == cls.BANNED.value:
            return 'Забанен'
        elif status == cls.REPLACEABLE.value:
            return 'Может быть заменен'
        elif status == cls.NOT_RUNNING.value:
            return 'Не запущен'
        elif status == cls.JOINING.value:
            return 'Присоединяется'
        elif status == cls.RUNNING.value:
            return 'Запущен'
        else:
            return 'Неизвестный статус'


class ChannelStatusEnum(Enum):
    OK = 1
    PRIVATE = 2


class UserStatusEnum(Enum):
    BANNED = 0
    OK = 1
    ADMIN = 555
    MAIN_ADMIN = 777


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
    answer_posts = Column(Integer(), default=2)
    is_premium = Column(Boolean(), default=False)
    is_reacting = Column(Boolean(), default=False)
    send_as = Column(String(255), nullable=True)
    is_neuro = Column(Boolean, default=False)
    text = Column(String, nullable=True)
    comment_communications = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey('user.chat_id'), nullable=True)
    owner = relationship('User', back_populates='sessions')

    def __repr__(self):
        return f'Client <{self.session_id}, {self.status}>'

    def __str__(self):
        return f'@{self.username} {self.first_name} {self.last_name}'


class User(Base):
    __tablename__ = 'user'

    chat_id = Column(Integer, primary_key=True)
    status = Column(Integer, nullable=False, default=UserStatusEnum.OK.value)
    sessions = relationship('TgClient', back_populates='owner')


class Poem(Base):
    __tablename__ = 'poem'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=False)
    is_sent = Column(Boolean, default=False)
    serial_number = Column(Integer, nullable=False)

    def __str__(self):
        return f"{self.id},{self.text[:min(20, len(str(self.text)))]}"
