from __future__ import absolute_import
from __future__ import print_function
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import win32traceutil
import win32serviceutil
import win32service
import win32event
import sys
import os

print('starting')


def makepath(*paths):
    dir = os.path.join(*paths)
    dir = os.path.abspath(dir)
    return dir, os.path.normcase(dir)


def _init_pathinfo():
    """Return a set containing all existing directory entries from sys.path"""
    d = set()
    for dir in sys.path:
        try:
            if os.path.isdir(dir):
                dir, dircase = makepath(dir)
                d.add(dircase)
        except TypeError:
            continue
    return d


def addpackage(sitedir, name, known_paths):
    """Add a new path to known_paths by combining sitedir and 'name' or execute
    sitedir if it starts with 'import'"""
    if known_paths is None:
        _init_pathinfo()
        reset = 1
    else:
        reset = 0
    fullname = os.path.join(sitedir, name)
    try:
        f = open(fullname, "rU")
    except IOError:
        return
    try:
        for line in f:
            if line.startswith("#"):
                continue
            if line.startswith("import"):
                exec(line)
                continue
            line = line.rstrip()
            dir, dircase = makepath(sitedir, line)
            if not dircase in known_paths and os.path.exists(dir):
                sys.path.append(dir)
                known_paths.add(dircase)
    finally:
        f.close()
    if reset:
        known_paths = None
    return known_paths


def addsitedir(sitedir, known_paths=None):
    """Add 'sitedir' argument to sys.path if missing and handle .pth files in
    'sitedir'"""
    if known_paths is None:
        known_paths = _init_pathinfo()
        reset = 1
    else:
        reset = 0
    sitedir, sitedircase = makepath(sitedir)
    if not sitedircase in known_paths:
        sys.path.append(sitedir)        # Add path component
    try:
        names = os.listdir(sitedir)
    except os.error:
        return
    names.sort()
    for name in names:
        if name.endswith(os.extsep + "pth"):
            addpackage(sitedir, name, known_paths)
    if reset:
        known_paths = None
    return known_paths


class PasteWinService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CIOCOfflineTools"
    _svc_display_name_ = "CIOC Offline Tools"
    _svc_description_ = "CIOC Offline Tools"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcDoRun(self):

        app_dir = os.path.dirname(sys.executable)
        cfg_file = os.path.join(app_dir, 'production.ini')

        print(app_dir)

        os.chdir(app_dir)
        paths = [app_dir]
        addsitedir(os.path.join(app_dir, 'site-packages'))

        sys.path[0:0] = paths
        print(sys.path)

        from paste.script.serve import ServeCommand as Server
        s = Server(None)
        args = [cfg_file]

        s.run(args)
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        "send stop event"
        win32event.SetEvent(self.stop_event)
        "stop event sent"
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        "Exit"
        sys.exit()

if __name__ == '__main__':
    # Note that this code will not be run in the 'frozen' exe-file!!!
    win32serviceutil.HandleCommandLine(PasteWinService)
