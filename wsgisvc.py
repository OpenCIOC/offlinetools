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

# This file contains some sourc code from site.py from the Python source which
# bootstraps the site-packages directory. It is marked by begin and end comments

from __future__ import absolute_import
from __future__ import print_function

import sys

# import win32traceutil
import win32serviceutil
import win32service
import win32event
import os
import io


class PasteWinService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CIOCOfflineTools2"
    _svc_display_name_ = "CIOC Offline Tools 2.0"
    _svc_description_ = "CIOC Offline Tools 2.0"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcDoRun(self):

        app_dir = os.path.dirname(sys.executable)
        cfg_file = os.path.join(app_dir, 'production.ini')
        debug = False
        if 'debug' in sys.argv:
            debug = True
            cfg_file = os.path.join(app_dir, 'development.ini')

        os.chdir(app_dir)
        paths = [app_dir]
        addsitedir(os.path.join(app_dir, 'site-packages'))

        sys.path[0:0] = paths

        from paste.deploy import loadapp
        from paste.httpserver import serve


        app = loadapp('config:' + cfg_file, 'main', relative_to=os.getcwd(), global_conf={})
        self.server = serve(app, port=8765, start_loop=False)
        self.server.serve_forever()

        if not debug:
            win32event.SetEvent(self.stop_event)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        "send stop event"
        self.server.server_close()
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        "stop event sent"

# ==========================================================================
# start of inlined methods from site.py to bootstrap site-packages directory
# covered by PSF license from Python distribution
# ==========================================================================


def makepath(*paths):
    dir = os.path.join(*paths)
    try:
        dir = os.path.abspath(dir)
    except OSError:
        pass
    return dir, os.path.normcase(dir)


def _init_pathinfo():
    """Return a set containing all existing file system items from sys.path."""
    d = set()
    for item in sys.path:
        try:
            if os.path.exists(item):
                _, itemcase = makepath(item)
                d.add(itemcase)
        except TypeError:
            continue
    return d


def addpackage(sitedir, name, known_paths):
    """Process a .pth file within the site-packages directory:
       For each line in the file, either combine it with sitedir to a path
       and add that to known_paths, or execute it if it starts with 'import '.
    """
    if known_paths is None:
        known_paths = _init_pathinfo()
        reset = True
    else:
        reset = False
    fullname = os.path.join(sitedir, name)
    try:
        f = io.TextIOWrapper(io.open_code(fullname))
    except OSError:
        return
    with f:
        for n, line in enumerate(f):
            if line.startswith("#"):
                continue
            try:
                if line.startswith(("import ", "import\t")):
                    exec(line)
                    continue
                line = line.rstrip()
                dir, dircase = makepath(sitedir, line)
                if not dircase in known_paths and os.path.exists(dir):
                    sys.path.append(dir)
                    known_paths.add(dircase)
            except Exception:
                print("Error processing line {:d} of {}:\n".format(n+1, fullname),
                      file=sys.stderr)
                import traceback
                for record in traceback.format_exception(*sys.exc_info()):
                    for line in record.splitlines():
                        print('  '+line, file=sys.stderr)
                print("\nRemainder of file ignored", file=sys.stderr)
                break
    if reset:
        known_paths = None
    return known_paths


def addsitedir(sitedir, known_paths=None):
    """Add 'sitedir' argument to sys.path if missing and handle .pth files in
    'sitedir'"""
    if known_paths is None:
        known_paths = _init_pathinfo()
        reset = True
    else:
        reset = False
    sitedir, sitedircase = makepath(sitedir)
    if not sitedircase in known_paths:
        sys.path.append(sitedir)        # Add path component
        known_paths.add(sitedircase)
    try:
        names = os.listdir(sitedir)
    except OSError:
        return
    names = [name for name in names if name.endswith(".pth")]
    for name in sorted(names):
        addpackage(sitedir, name, known_paths)
    if reset:
        known_paths = None
    return known_paths

# ==========================================================================
# end of inlined methods from site.py to bootstrap site-packages directory
# covered by PSF license from Python distribution
# ==========================================================================

if __name__ == '__main__':
    # Note that this code will not be run in the 'frozen' exe-file!!!
    win32serviceutil.HandleCommandLine(PasteWinService)
