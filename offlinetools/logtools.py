# =========================================================================================
#  Copyright 2016 Community Information Online Consortium (CIOC) and KCL Software Solutions
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# =========================================================================================

from __future__ import absolute_import
import os
import logging.handlers

import ctypes
from ctypes import wintypes, windll, create_unicode_buffer

CSIDL_COMMON_APPDATA = 35
_SHGetFolderPath = windll.shell32.SHGetFolderPathW
_SHGetFolderPath.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.HANDLE, wintypes.DWORD, wintypes.LPCWSTR]
_app_data_dir = None


def _get_app_data_dir():
    global _app_data_dir

    if _app_data_dir is None:
        path_buf = create_unicode_buffer(wintypes.MAX_PATH)
        _ = _SHGetFolderPath(0, CSIDL_COMMON_APPDATA, 0, 0, path_buf)
        common_appdata_path = path_buf.value
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
