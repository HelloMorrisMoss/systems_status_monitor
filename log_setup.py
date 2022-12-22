"""Contains the logger setup and a simple script to read the log file into a pandas dataframe."""
import logging
import sys
from logging.handlers import RotatingFileHandler

from untracked_config.development_node import ON_DEV_NODE


class BreadcrumbFilter(logging.Filter):
    """Provides %(breadcrumbs) field for the logger formatter.

    Th breadcrumbs field returns module.funcName.lineno as a single string.
     example:
        formatters={
        'console_format': {'format':
                           '%(asctime)-30s %(breadcrumbs)-35s %(levelname)s: %(message)s'}
                   }
       self.logger.debug('handle_accept() -> %s', client_info[1])
        2020-11-08 14:04:40,561        echo_server03.handle_accept.24      DEBUG: handle_accept() -> ('127.0.0.1',
        49515)
    """

    def filter(self, record):
        record.breadcrumbs = "{}.{}.{}".format(record.module, record.funcName, record.lineno)
        return True


def setup_logger():
    # set up the base logger
    logr = logging.getLogger()
    base_log_level = logging.DEBUG if ON_DEV_NODE else logging.INFO
    logr.setLevel(base_log_level)

    # console logger
    c_handler = logging.StreamHandler()
    c_handler.setLevel(base_log_level)
    c_format = logging.Formatter('%(asctime)-30s %(breadcrumbs)-45s %(levelname)s: %(message)s')
    c_handler.setFormatter(c_format)
    c_handler.addFilter(BreadcrumbFilter())
    logr.addHandler(c_handler)

    # file logger
    f_handler = RotatingFileHandler('mahlo_popup.log', maxBytes=2000000)
    f_handler.setLevel(base_log_level)
    f_string = '"%(asctime)s","%(name)s", "%(breadcrumbs)s","%(funcName)s","%(lineno)d","%(levelname)s","%(message)s"'
    f_format = logging.Formatter(f_string)
    f_handler.addFilter(BreadcrumbFilter())
    f_handler.setFormatter(f_format)
    logr.addHandler(f_handler)

    def handle_exception(exc_type, exc_value, exc_traceback):
        """Log unhandled exceptions."""

        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logr.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    return logr


if __name__ != '__main__':
    # protect against multiple loggers from importing in multiple files
    lg = setup_logger() if not logging.getLogger().hasHandlers() else logging.getLogger()
# else:
#     import pandas as pd
#
#     column_names = ['tstamp', 'program', 'breadcrumbs', 'callable', 'line#', 'level',
#                     'message']  # + [f'col{n}' for n in range(8)]
#     ldf = pd.read_csv('untracked_config/20220321 mahlo lam1 log - mahlo_popup.log', names=column_names)
#     col_name = 'tstamp'
#     ldf = ldf[len(ldf) - 5000::]
#     ldf[col_name] = pd.to_datetime(ldf[col_name])
#
#     ldf = ldf[ldf['tstamp'] > '2022-03-18']
