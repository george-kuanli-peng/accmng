import os
import sqlite3

from typing import List

from libs import config
from libs import backends


__user_visible_attrs = {'uid', 'username', 'fullname', 'email'}
__db_conn = None


def _get_db_path() -> str:
    rel_path = config.get_value('SYSTEM', 'DB_PATH')
    return os.path.join(os.path.dirname(__file__), '..', rel_path)


def _check_db_file_exists() -> bool:
    db_path = _get_db_path()
    return os.path.isfile(db_path)


def init_db():
    """Create new DB if it does not exist; create new DB table if it does not exist"""
    db_path = _get_db_path()

    if _check_db_file_exists():
        # TODO: logging
        print('DB files %s already exists; reuse the current one.' % db_path)
    else:
        # TODO: logging
        print('DB file %s does not exist; create a new one.' % db_path)

    conn = sqlite3.connect(db_path)
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS USERS (
        uid       INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        username  VARCHAR(63) UNIQUE NOT NULL,
        fullname  VARCHAR(63) NOT NULL,
        email     VARCHAR(127) NOT NULL
    );
    ''')

    backends.db_init_tables(conn)

    conn.commit()
    conn.close()


def get_db_conn() -> sqlite3.Connection:
    global __db_conn

    if __db_conn:
        return __db_conn

    db_path = _get_db_path()

    if _check_db_file_exists():
        __db_conn = sqlite3.connect(db_path)
        return __db_conn

    raise Exception('Cannot open db: %s does not exist' % db_path)


def close_db_conn():
    global __db_conn
    if __db_conn:
        __db_conn.close()
        __db_conn = None


def _check_user_exists(username: str) -> bool:
    conn = get_db_conn()

    try:
        cur = conn.execute('SELECT COUNT(*) FROM USERS WHERE username=?', (username,))
        return int(cur.fetchone()[0]) == 1
    except conn.Error:
        conn.execute('ROLLBACK')
        raise


def get_uid(username: str) -> int:
    conn = get_db_conn()
    if not _check_user_exists(username):
        raise ValueError('user %s does not exist' % username)
    uid = conn.execute('SELECT uid FROM USERS WHERE username=?', (username,)).fetchone()[0]
    return uid


def get_user(uid: int, get_attrs: List[str] = None) -> dict:
    if get_attrs:
        get_attrs = [attr for attr in get_attrs if attr in __user_visible_attrs]
    else:
        get_attrs = list(__user_visible_attrs)

    conn = get_db_conn()
    cur = conn.execute('''SELECT %s FROM USERS WHERE uid=?''' % ','.join(get_attrs), (uid,))
    try:
        row = cur.fetchone()
        attrs = {col_names[0]: row[col_idx] for col_idx, col_names in enumerate(cur.description)}
        return attrs
    except TypeError:
        raise ValueError('user %d does not exist' % uid)


def apply_user(username: str, fullname: str = None, email: str = None, **kwargs):
    conn = get_db_conn()

    try:
        conn.execute('BEGIN')

        if _check_user_exists(username):
            # update user
            uid = get_uid(username)
            if fullname is not None:
                conn.execute('''UPDATE USERS SET fullname=? WHERE uid=?''', (fullname, uid))
            if email is not None:
                conn.execute('''UPDATE USERS SET email=? WHERE uid=?''', (email, uid))
        else:
            # insert user
            if fullname is None:
                raise ValueError('fullname is empty')
            if email is None:
                raise ValueError('email is empty')

            uid = conn.execute('''INSERT INTO
                    USERS  (username, fullname, email)
                    VALUES (?,?,?,?)''', (username, fullname, email)).lastrowid

        backends.db_apply_user(conn, username=username, uid=uid, **kwargs)

        conn.commit()
    except (conn.Error, ValueError):
        conn.execute('ROLLBACK')
        raise
