import asyncio
import random
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telethon import TelegramClient
from telethon.tl.custom import Dialog
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import Channel
from telethon.utils import get_peer

from client import Client
# from client import Client
from config import channel_logins
import db.funcs as db
from db.models import TgChannel


# client = TelegramClient('sessions/12093135631/12093135631.session', 2040, 'b18441a1ff607e10a989891a5462e627',
#                         # proxy=proxy.dict,
#                         device_model="iPhone 13 Pro Max",
#                         system_version="14.8.1",
#                         app_version="8.4",
#                         lang_code="en",
#                         system_lang_code="en-US"
#                         )


async def main():
    cli = Client('12098898404', 0, ['bugulma', 'aznakaevo'])
    await cli.run()


asyncio.run(main())
