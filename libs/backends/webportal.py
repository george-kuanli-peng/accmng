import datetime
import enum
import sqlite3

from libs import config
import libs.db


__default_user_action_valid_period = None


def get_default_user_action_valid_period():
    global __default_user_action_valid_period
    if __default_user_action_valid_period is not None:
        return __default_user_action_valid_period

    try:
        __default_user_action_valid_period = int(config.get_value('WEB_PORTAL', 'DEF_USER_ACTION_VALID_PERIOD'))
    except (KeyError, TypeError):
        __default_user_action_valid_period = 1200
    return __default_user_action_valid_period


class UserAction(enum.IntEnum):
    FORGOT_PASS = 1


def db_init_table(conn: sqlite3.Connection):
    conn.executescript('''        
        CREATE TABLE IF NOT EXISTS WEB_USER_ACTION (
            aid          INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            uid          INTEGER NOT NULL,
            action_type  INTEGER NOT NULL,
            create_time  timestamp NOT NULL,
            valid_until  timestamp NOT NULL,
            closed       INTEGER NOT NULL DEFAULT 0,
            parm         TEXT NOT NULL DEFAULT "",
            FOREIGN KEY(uid) REFERENCES USERS(uid)
        );
        ''')


# noinspection PyUnusedLocal
def db_apply_user(conn: sqlite3.Connection, username: str, uid: int = None, **kwargs):
    pass


def create_user_action(uid: int, action_type: UserAction, parm: str = None, valid_period: float = None):
    if parm is None:
        parm = ''
    if valid_period is None:
        valid_period = get_default_user_action_valid_period()

    create_time = datetime.datetime.now()
    valid_until = create_time + datetime.timedelta(seconds=valid_period)

    conn = libs.db.get_db_conn()
    conn.execute('''INSERT INTO
        WEB_USER_ACTION (uid, action_type, create_time, valid_until, parm)
        VALUES (?,?,?,?,?)''',
                 (uid, action_type, create_time, valid_until, parm))

    return {
        'valid_period': valid_period,
        'valid_until': valid_until
    }


# noinspection PyUnusedLocal
def apply_user(username: str, **kwargs):
    pass
