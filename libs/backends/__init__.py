import importlib.util
import libs.config
import os.path
import re
import sqlite3


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


def apply_user(username: str, **kwargs):
    for backend_mod in _get_backends():
        backend_mod.apply_user(username=username, **kwargs)


def db_init_tables(conn: sqlite3.Connection):
    for backend_mod in _get_backends():
        backend_mod.db_init_table(conn)


def db_apply_user(conn: sqlite3.Connection, username: str, uid: int = None, **kwargs):
    for backend_mod in _get_backends():
        backend_mod.db_apply_user(conn, username=username, uid=uid, **kwargs)
