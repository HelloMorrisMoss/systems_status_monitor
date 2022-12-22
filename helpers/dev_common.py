"""For development helpers, in their own module to avoid circular imports and keep things organized."""
import datetime
import os
import sys

from log_setup import lg


def dt_to_shift(dtime: datetime.datetime):
    """Convert a datetime.datetime to the shift that it would correspond to.

    :param dtime: datetime.datetime
    :return: int, the shift
    """

    now = dtime
    seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    if seconds_since_midnight < 26_100:
        return 3
    elif seconds_since_midnight < 54_900:
        return 1
    elif seconds_since_midnight < 83_700:
        return 2
    else:
        return 3


def touch(file_path):
    """Create an empty file at the file path."""

    with open(file_path, 'w') as pf:
        pf.write('')


def blank_up(file_path, after_backup_function=touch):
    """Backup the file with a timestamp and replace with a blank file."""

    import time

    timestr = time.strftime("%Y%m%d-%H%M%S")
    fp, ext = os.path.splitext(file_path)
    new_fp = f'{fp}_BACKUP_{timestr}{ext}'
    os.rename(file_path, new_fp)
    lg.info('Backing up last_position.txt to %s', new_fp)
    touch(file_path)


def restart_program():
    """Restarts the program with the same command line arguments it was started with."""

    os.execl(sys.executable, sys.executable, *sys.argv)


def exception_one_line(exception_obj):
    """Get the exception traceback text as a one line string. New lines are replaces with escaped '\\n'.

    :param exception_obj: builtins.Ex.ception, the exception.
    :return: str, the message string.
    """
    from traceback import format_exception
    return ''.join(format_exception(FileNotFoundError, exception_obj, exception_obj.__traceback__)
                   ).replace('\n', '\\n')
