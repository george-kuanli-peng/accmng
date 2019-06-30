import subprocess
from typing import List


SMB_DEFAULT_GROUP = 'sambashare'


def add_user(username: str, password: str, force_create: bool =False,
             extra_smb_groups: List(str) =[], no_default_smb_group: bool =False, **kwargs):
    """Add user

    Args:
        username: username
        password: password
        force_create: update user when it already exists; by default, it fails
        extra_smb_groups: extra groups besides default samba group to add
        no_default_smb_group: do not include default samba group; by default, it includes
    """
    if no_default_smb_group:
        smb_groups = extra_smb_groups
    else:
        smb_groups = [SMB_DEFAULT_GROUP] + [g for g in extra_smb_groups if g != SMB_DEFAULT_GROUP]

    try:
        # create user
        subprocess.run(['sudo', 'useradd',
                        '--no-create-home',
                        '-s', '/usr/sbin/nologin',
                        '-G', ','.join(smb_groups),
                        username],
                       check=True)
        # set samba password
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
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise
