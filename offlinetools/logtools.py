import os
import logging.handlers

from win32com.shell import shell, shellcon

_app_data_dir = None

def _get_app_data_dir():
    global _app_data_dir


    if _app_data_dir is None:
        common_appdata_path =  shell.SHGetFolderPath (0, shellcon.CSIDL_COMMON_APPDATA, 0, 0)
        _app_data_dir = os.path.join(common_appdata_path, 'CIOC', 'OfflineTools')
        try:
            os.makedirs(_app_data_dir)
        except os.error:
            pass


    return _app_data_dir

class TimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    def __init__(self, name):
        global _log_root

        app_data_dir = _get_app_data_dir()
        log_dir = os.path.join(app_data_dir, 'logs')

        try:
            os.makedirs(log_dir)
        except os.error:
            pass

        logfile = os.path.join(log_dir, name)

        logging.handlers.TimedRotatingFileHandler.__init__(self, logfile, 'midnight', delay=True)


