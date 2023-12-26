import os
import shutil
import traceback
from zipfile import ZipFile

from client import Client
import db.funcs as db
from config import logger, TEMP_PROXY
from db.models import ClientStatusEnum


def read_archive_sessions(archive_path):
    try:
        shutil.rmtree('data/temp_sessions')
        os.makedirs('data/temp_sessions')
        with ZipFile(archive_path, "r") as myzip:
            myzip.extractall('data/temp_sessions')
    except Exception as ex:
        logger.error(traceback.format_exc())
        print(traceback.format_exc())


async def add_temp_sessions(update_olds=False):
    sessions = os.listdir('data/temp_sessions')
    new = 0
    banned = 0
    old = 0
    errors = []
    for session_id in sessions:
        try:
            if not (os.path.exists(f'data/temp_sessions/{session_id}/{session_id}.json') and os.path.exists(f'data/temp_sessions/{session_id}/{session_id}.session')):
                errors.append(f'incorrect {session_id}')
            else:
                client = Client(session_id, TEMP_PROXY, temp=True, debug=True)
                await client.init_session()
                f = await client.start()
                db_me = await db.get_client(session_id)
                print(db_me)
                if f:
                    me = await client.client.get_me()
                    await client.disconnect()
                    print(me)
                    print(me.username, me.first_name, me.last_name, me.premium)
                    if db_me is None:
                        await db.insert_client(session_id)
                        await db.update_data(session_id, username=me.username, first_name=me.first_name,
                                             last_name=me.last_name, is_premium=me.premium)
                        new += 1
                        shutil.move(f'data/temp_sessions/{session_id}', f'sessions/{session_id}')
                    else:
                        old += 1
                        if update_olds:
                            await db.update_data(session_id, username=me.username, first_name=me.first_name, last_name=me.last_name, is_premium=me.premium)
                else:
                    await client.disconnect()
                    banned += 1
                    await db.set_status(session_id, ClientStatusEnum.BANNED)
                    shutil.move(f'data/temp_sessions/{session_id}', f'sessions_banned/{session_id}')
        except Exception as ex:
            logger.error(traceback.format_exc())
            errors.append(f'{session_id} - {ex}')
    return {'new': new, 'old': old, 'banned': banned, 'errors': errors}

