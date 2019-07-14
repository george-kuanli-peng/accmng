import os
import sqlite3

import config


__db_conn = None


def _get_db_path() -> str:
    rel_path = config.get_value('SYSTEM', 'DB_PATH')
    return os.path.join(os.path.dirname(__file__), rel_path)


def create_db():
    db_path = _get_db_path()

    if os.path.exists(db_path):
        raise Exception('Cannot create db: %s already exists' % db_path)

    conn = sqlite3.connect(db_path)
    conn.executescript('''
    CREATE TABLE USERS (
        uid       INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        username  VARCHAR(63) UNIQUE NOT NULL,
        password  VARCHAR
    );
    ''')
    conn.commit()
    conn.close()


def _get_db_conn() -> sqlite3.Connection:
    global __db_conn

    if __db_conn:
        return __db_conn
    __db_conn = sqlite3.connect(_get_db_path())
    return __db_conn


def _close_db_conn():
    conn = _get_db_conn()
    if conn:
        conn.close()


def add_user(username: str, password: str):
    # TODO: encrypt password
    conn = _get_db_conn()
    conn.execute('''INSERT INTO
    USERS  (username, password)
    VALUES (?,?)''', (username, password))
    conn.commit()
