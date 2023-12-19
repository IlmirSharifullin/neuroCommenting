from aiogram import Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import *
from bot.keyboards import *

router = Router(name='callbacks-router')
