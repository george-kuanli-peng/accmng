import pwd
import sqlite3
import subprocess
from typing import List

import libs.db


SMB_GROUPS = [
    'sambashare',
    'sadmin',
    'sambaro'
]
SMB_DEFAULT_GROUP = 'sambashare'


def _check_user_exists(username: str):
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False


def _get_sys_groups(username: str):
    cur_sys_groups = subprocess.check_output(
        ['sudo', 'groups', username],
        universal_newlines=True
    ).split(':')[1].strip().split(' ')
    return cur_sys_groups


def _get_sys_primary_group(username: str):
    primary_sys_group = subprocess.check_output(
        ['sudo', 'id', '-gn', username],
        universal_newlines=True
    ).strip()
    return primary_sys_group


def _get_smb_groups(extra_smb_groups: List[str], no_default_smb_group: bool):
    if no_default_smb_group:
        smb_groups = extra_smb_groups
    else:
        smb_groups = [SMB_DEFAULT_GROUP] + [g for g in extra_smb_groups if g != SMB_DEFAULT_GROUP]
    return smb_groups


def _set_smb_password(username: str, password: str):
    p1 = subprocess.Popen(['echo', '-ne', '%s\n%s\n' % (password, password)],
                          stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['sudo', 'smbpasswd', '-a', '-s', username],
                          stdin=p1.stdout,
                          stdout=subprocess.PIPE)
    p1.stdout.close()
    output = p2.communicate()
    if p2.returncode != 0:
        raise subprocess.CalledProcessError(p2.returncode, 'smbpasswd', output[0], output[1])
    # activate samba user
    subprocess.run(['sudo', 'smbpasswd', '-e', username],
                   check=True)


# noinspection PyUnusedLocal
def add_user(username: str, password: str, force_create: bool =False,
             extra_smb_groups: List[str] =None, no_default_smb_group: bool =False, **kwargs):
    """Add user

    Args:
        username: username
        password: password
        extra_smb_groups: extra groups besides default samba group to add
        no_default_smb_group: do not include default samba group; by default, it includes
    """
    if _check_user_exists(username):
        raise Exception('Cannot create user %s: already exists' % username)

    if extra_smb_groups is None:
        extra_smb_groups = []

    try:
        # create user
        smb_groups = _get_smb_groups(extra_smb_groups, no_default_smb_group)
        subprocess.run(['sudo', 'useradd',
                        '--no-create-home',
                        '-s', '/usr/sbin/nologin',
                        '-G', ','.join(smb_groups),
                        username],
                       check=True)
        # set samba password
        _set_smb_password(username, password)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise


# noinspection PyUnusedLocal
def mod_user(username: str, password: str =None,
             extra_smb_groups: List[str] =None, no_default_smb_group: bool = False, **kwargs):
    """Modify user

    Args:
        username: username
        password: password to set if provided
        extra_smb_groups: extra groups besides default samba group to set if provided
        no_default_smb_group: do not include default samba group; by default, it includes
    """
    mod_password = password is not None
    mod_smb_groups = extra_smb_groups is not None
    mod_any = mod_password or mod_smb_groups
    if not mod_any:
        return

    try:
        # modify user
        cmds = ['sudo', 'usermod']
        if mod_smb_groups:
            smb_groups = set(_get_smb_groups(extra_smb_groups, no_default_smb_group))
            cur_sys_groups = set(_get_sys_groups(username))
            new_sys_groups = cur_sys_groups.difference(set(SMB_GROUPS)).union(smb_groups)
            cmds.extend(['-G', ','.join(new_sys_groups)])

            cur_sys_primary_group = _get_sys_primary_group(username)
            if cur_sys_primary_group not in new_sys_groups:
                if not no_default_smb_group and SMB_DEFAULT_GROUP:
                    cmds.extend(['-g', SMB_DEFAULT_GROUP])
                elif len(new_sys_groups) > 0:
                    cmds.extend(['-g', list(new_sys_groups)[0]])
                else:
                    raise Exception('Cannot set initial group for user %s: empty membership groups' % username)

            cmds.append(username)
            subprocess.run(cmds, check=True)

        if mod_password:
            _set_smb_password(username, password)

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise


# noinspection PyUnusedLocal
def apply_user(username: str, password: str =None,
               extra_smb_groups: List[str] =None, no_default_smb_group: bool =False, **kwargs):
    """Add user or modify user

    Args:
        username: username
        password: password
        extra_smb_groups: extra groups besides default samba group to add
        no_default_smb_group: do not include default samba group; by default, it includes
    """
    if _check_user_exists(username):
        mod_user(username=username,
                 password=password,
                 extra_smb_groups=extra_smb_groups,
                 no_default_smb_group=no_default_smb_group)
    else:
        add_user(username=username,
                 password=password if password is not None else '',
                 extra_smb_groups=extra_smb_groups,
                 no_default_smb_group=no_default_smb_group)


def _db_check_user_exists(conn: sqlite3.Connection, username: str) -> bool:
    try:
        cur = conn.execute('SELECT uid FROM USERS WHERE username=?', (username,))
        uid = int(cur.fetchone()[0])
        cur.execute('SELECT COUNT(*) FROM SAMBA WHERE uid=?', (uid,))
        return int(cur.fetchone()[0]) == 1
    except conn.Error:
        raise
    except TypeError:
        # probably uid is not found (cur.fetchone() is None)
        return False


def db_init_table(conn: sqlite3.Connection):
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS SAMBA (
            uid       INTEGER UNIQUE NOT NULL,
            groups    VARCHAR(127) NOT NULL,
            FOREIGN KEY(uid) REFERENCES USERS(uid)
        );
        ''')


# noinspection PyUnusedLocal
def db_apply_user(conn: sqlite3.Connection, username: str, uid: int = None, samba_grps: List[str] = None, **kwargs):
    if uid is not None:
        uid = libs.db.get_uid(username)

    if _db_check_user_exists(conn, username):
        # update user
        if samba_grps is not None:
            conn.execute('''UPDATE SAMBA SET groups=? WHERE uid=?''', (','.join(samba_grps), uid))
    else:
        # insert user
        if samba_grps is None:
            raise ValueError('samba groups are empty')

        conn.execute('''INSERT INTO
            SAMBA  (uid, groups)
            VALUES (?,?)''', (uid, ','.join(samba_grps) if samba_grps else ''))
