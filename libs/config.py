import configparser
import os


__config = None


def init_config(path):
    global __config

    if not __config:
        __config = configparser.ConfigParser()
        # TODO: logging
        print('Read config file: ' + path)
        __config.read(path)
        # TODO: required attributes checking


def get_value(section: str, option: str):
    global __config

    try:
        env_key = '_'.join([section.upper(), option.upper()])
        return os.environ[env_key]
    except KeyError:
        return __config[section][option]
