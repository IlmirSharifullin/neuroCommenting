import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from utils.logger import setup_logger, log_to_channel

load_dotenv()

DB_URL = os.getenv('DB_URL')
TEMP_PROXY = os.getenv('TEMP_PROXY')

engine = create_async_engine(url=DB_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

logger = setup_logger()
