import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_LIST = [901977201]

LOGS_CHANNEL_ID = os.getenv('LOGS_CHANNEL_ID')

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_URL = os.getenv('DB_URL')

WEB_SERVER_HOST = os.getenv('WEB_SERVER_HOST')
WEB_SERVER_PORT = int(os.getenv('WEB_SERVER_PORT'))
BASE_WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
