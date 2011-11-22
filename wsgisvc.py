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


#import win32traceutil
import win32serviceutil
import win32service
import win32event
import sys
import os


class PasteWinService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CIOCOfflineTools"
    _svc_display_name_ = "CIOC Offline Tools"
    _svc_description_ = "CIOC Offline Tools"

    
    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcDoRun(self):

        app_dir = os.path.dirname(sys.executable)
        cfg_file = os.path.join(app_dir, 'production.ini')

        print app_dir

        os.chdir(app_dir)
        paths = [app_dir]
        for pthfile, slc in [('setuptools.pth', slice(1)), ('easy-install.pth', slice(1,-1))]:
            with open(os.path.join(app_dir, 'site-packages', pthfile), 'r') as f:
                paths.extend(os.path.join(app_dir, 'site-packages', x.strip()) for x in f.readlines()[slc])

        sys.path[0:0] = paths


        from paste.script.serve import ServeCommand as Server
        s = Server(None)
        args = [ cfg_file ]

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


if __name__=='__main__':
    # Note that this code will not be run in the 'frozen' exe-file!!!
    win32serviceutil.HandleCommandLine(PasteWinService)
