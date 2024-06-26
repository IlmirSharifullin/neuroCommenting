import logging
import os

import requests

LOGS_CHANNEL_ID = os.getenv('LOGS_CHANNEL_ID')


def log_to_channel(msg, type='info'):
    res = requests.post('https://api.telegram.org/bot6621958158:AAFIALtB_WkdK1YbXZ_dBfkLxzVR6xAjPK0/sendMessage',
                        params={'text': ('ERROR:\n' if type == 'error' else 'INFO:\n') + str(msg),
                                'chat_id': LOGS_CHANNEL_ID})
    return res.content


class CustomLogger(logging.Logger):
    def info(self, msg, *args, to_channel=True, **kwargs):
        super().info(msg, *args, **kwargs)
        if to_channel:
            res = log_to_channel(msg, 'info')

    def error(self, msg, *args, to_channel=True, **kwargs):
        super().error(msg, *args, **kwargs)
        if to_channel:
            res = log_to_channel(msg, 'error')


def setup_logger():
    logging.basicConfig(level=int(os.getenv("LOG_LEVEL", 10)),
                        format='%(asctime)s - %(levelname)s - %(name)s- %(message)s')

    return CustomLogger(__name__)
