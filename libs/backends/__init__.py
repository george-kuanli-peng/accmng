import crypt
import os.path
import re
import sqlite3
import spwd

import importlib.util

import libs.config
import libs.db


_backends = None


def _get_backends():
    global _backends

    if _backends is not None:
        return _backends

    _backends = []
    backends_root = os.path.abspath(os.path.dirname(__file__))
    for mod_sec in re.split(r'\s*[,]\s*', libs.config.get_value('SYSTEM', 'ENABLE_MODULES')):
        mod_name = libs.config.get_value(mod_sec, 'MOD_NAME')
        spec = importlib.util.spec_from_file_location(
            'libs.backends.' + mod_name,
            os.path.join(backends_root, mod_name + '.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _backends.append(mod)
    return _backends


def auth_user_pass(username: str, password: str) -> bool:
    """Check whether the username is active and the password matches
       Ref: Python Enter Password And Compare to Shadowed Password Database
       https://stackoverflow.com/questions/15846931/python-enter-password-and-compare-to-shadowed-password-database
    """
    try:
        enc_pwd = spwd.getspnam(username)[1]
        if enc_pwd in ['NP', '!', '', None]:
            # no password set
            return password is None or password == ''
        if enc_pwd in ['LK', '*']:
            # account is locked
            return False
        if enc_pwd == '!!':
            # password is expired
            return False
        return crypt.crypt(password, enc_pwd) == enc_pwd
    except KeyError:
        # user not found
        return False


def auth_user_mail(username: str, email: str) -> bool:
    try:
        uid = libs.db.get_uid(username)
        user_info = libs.db.get_user(uid, ['email'])
        return user_info['email'] == email
    except ValueError:
        return False


def apply_user(username: str, **kwargs):
    for backend_mod in _get_backends():
        backend_mod.apply_user(username=username, **kwargs)


def db_init_tables(conn: sqlite3.Connection):
    for backend_mod in _get_backends():
        backend_mod.db_init_table(conn)


def db_apply_user(conn: sqlite3.Connection, username: str, uid: int = None, **kwargs):
    for backend_mod in _get_backends():
        backend_mod.db_apply_user(conn, username=username, uid=uid, **kwargs)
