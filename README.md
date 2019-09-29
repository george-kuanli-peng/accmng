# accmng
Integrated account management for multiple systems

## Installation

System requirements:

1. Python 3.6+
1. A system account with password-less sudoer's privileges

Python package requirements:

```bash
pip install -r requirements.txt
```

## Execution

The simplest form:

```bash
python app.py
```

I will search the config file "config.ini" at the current execution directory first, or else at the program's (app.py) directory.

To specify another config file name or location:

```bash
python app.py --config_file=CUSTOM_CONFIG_FILE_PATH
```
