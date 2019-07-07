import pwd
import subprocess
from typing import List


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


def add_user(username: str, password: str, force_create: bool =False,
             extra_smb_groups: List[str] =None, no_default_smb_group: bool =False, **kwargs):
    """Add user

    Args:
        username: username
        password: password
        force_create: update user when it already exists; by default, it fails
        extra_smb_groups: extra groups besides default samba group to add
        no_default_smb_group: do not include default samba group; by default, it includes
    """
    if force_create:
        if _check_user_exists(username):
            mod_user(
                username=username,
                password=password,
                extra_smb_groups=extra_smb_groups,
                no_default_smb_group=no_default_smb_group
            )
    else:
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