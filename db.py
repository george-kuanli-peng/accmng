import os
import sqlite3
from typing import List

import config


__db_conn = None


def _get_db_path() -> str:
    rel_path = config.get_value('SYSTEM', 'DB_PATH')
    return os.path.join(os.path.dirname(__file__), rel_path)


def _get_db_file_exists() -> bool:
    db_path = _get_db_path()
    return os.path.isfile(db_path)


def create_db():
    if _get_db_file_exists():
        raise Exception('Cannot create db: %s already exists' % db_path)

    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.executescript('''
    CREATE TABLE USERS (
        uid       INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        username  VARCHAR(63) UNIQUE NOT NULL,
        password  VARCHAR
    );
    
    CREATE TABLE SAMBA (
        uid       INTEGER UNIQUE NOT NULL,
        groups    VARCHAR(127) NOT NULL,
        FOREIGN KEY(uid) REFERENCES USERS(uid)
    );
    ''')
    conn.commit()
    conn.close()


def _get_db_conn() -> sqlite3.Connection:
    global __db_conn

    if __db_conn:
        return __db_conn

    db_path = _get_db_path()

    if _get_db_file_exists():
        __db_conn = sqlite3.connect(db_path)
        return __db_conn

    raise Exception('Cannot open db: %s does not exist' % db_path)


def _close_db_conn():
    global __db_conn
    if __db_conn:
        __db_conn.close()
        __db_conn = None


def add_user(username: str, password: str, samba_grps: List[str] = None):
    # TODO: encrypt password
    conn = _get_db_conn()

    try:
        conn.execute('BEGIN')

        uid = conn.execute('''INSERT INTO
        USERS  (username, password)
        VALUES (?,?)''', (username, password)).lastrowid

        conn.execute('''INSERT INTO
        SAMBA  (uid, groups)
        VALUES (?,?)''', (uid, ','.join(samba_grps) if samba_grps else ''))

        conn.commit()
    except conn.Error:
        conn.execute('ROLLBACK')
        raise


def mod_user(username: str, password: str = None, samba_grps: List[str] = None):
    # TODO: encrypt password
    conn = _get_db_conn()

    try:
        conn.execute('BEGIN')

        uid = conn.execute('SELECT uid FROM USERS WHERE username=?', (username,)).fetchone()[0]

        if password is not None:
            conn.execute('''UPDATE USERS
            SET password=? WHERE uid=?''', (password, uid))

        if samba_grps is not None:
            conn.execute('''UPDATE SAMBA
            SET groups=? WHERE uid=?''', (','.join(samba_grps), uid))

        conn.commit()
    except conn.Error:
        conn.execute('ROLLBACK')
        raise
