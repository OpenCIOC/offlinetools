# -*- coding: utf-8 -*-
# this monkeypatches out the issue from https://github.com/py2exe/py2exe/issues/32
import py2exe

if py2exe.__version__ != '0.10.1.0' and py2exe.__version__ != '0.10.2.0':
    raise Exception('Expected py2exe version 0.10.1.0 or 0.10.2.0 and found version %s' % py2exe.__version__)

import py2exe.runtime

from py2exe.dllfinder import pydll

import imp
import io
import logging
import marshal
import os
import shutil
import sys
import zipfile

from py2exe.resources import UpdateResources

logger = logging.getLogger("runtime")

from importlib.machinery import EXTENSION_SUFFIXES
if '.pyd' in EXTENSION_SUFFIXES:
    EXTENSION_SUFFIXES = tuple(EXTENSION_SUFFIXES + ['.dll'])
else:
    raise AssertionError
from importlib.machinery import DEBUG_BYTECODE_SUFFIXES, OPTIMIZED_BYTECODE_SUFFIXES


RT_MANIFEST = 24


class Runtime(py2exe.runtime.Runtime):
    """This class represents the Python runtime: all needed modules
    and packages.  The runtime will be written to a zip.file
    (typically named pythonxy.zip) that can be added to sys.path.
    """

    def build_archive(self, libpath, delete_existing_resources=False):
        """Build the archive containing the Python library.
        """
        if self.options.bundle_files <= 1:
            # Add pythonXY.dll as resource into the library file
            #
            # XXX We should add a flag to the exe so that it does not try to load pythonXY.dll
            # from the file system.
            # XXX XXX XXX
            with UpdateResources(libpath, delete_existing=delete_existing_resources) as resource:
                with open(pydll, "rb") as ifi:
                    pydll_bytes = ifi.read()
                # We do not need to replace the winver string resource
                # in the python dll since it will be loaded via
                # MemoryLoadLibrary, and so python cannot find the
                # string resources anyway.
                if self.options.verbose > 1:
                    print("Add resource %s/%s(%d bytes) to %s"
                          % (os.path.basename(pydll), 1, len(pydll_bytes), libpath))
                resource.add(type=os.path.basename(pydll), name=1, value=pydll_bytes)

        if self.options.optimize:
            bytecode_suffix = OPTIMIZED_BYTECODE_SUFFIXES[0]
        else:
            bytecode_suffix = DEBUG_BYTECODE_SUFFIXES[0]

        if self.options.compress:
            compression = zipfile.ZIP_DEFLATED
        else:
            compression = zipfile.ZIP_STORED

        # Create a zipfile and append it to the library file
        arc = zipfile.ZipFile(libpath, "a",
                              compression=compression)

        # The same modules may be in self.ms.modules under different
        # keys; we only need one of them in the archive.
        for mod in set(self.mf.modules.values()):
            if mod.__code__:
                path =mod.__dest_file__
                stream = io.BytesIO()
                stream.write(imp.get_magic())
                if sys.version_info >= (3,7,0):
                    stream.write(b"\0\0\0\0") # null flags
                stream.write(b"\0\0\0\0") # null timestamp
                stream.write(b"\0\0\0\0") # null size
                marshal.dump(mod.__code__, stream)
                arc.writestr(path, stream.getvalue())

            elif hasattr(mod, "__file__"):
                the_extension_target_suffix = None
                for ext in EXTENSION_SUFFIXES:
                    if mod.__file__.endswith(ext):
                        the_extension_target_suffix = ext
                        break
                if the_extension_target_suffix is None:
                    raise RuntimeError(f"Module {mod.__file__} has unknown suffix, not in {EXTENSION_SUFFIXES!r}")
                if self.options.bundle_files <= 2:
                    # put .pyds into the archive
                    arcfnm = mod.__name__.replace(".", "\\") + the_extension_target_suffix
                    if self.options.verbose > 1:
                        print("Add %s to %s" % (os.path.basename(mod.__file__), libpath))
                    arc.write(mod.__file__, arcfnm)
                else:
                    # The extension modules will be copied into
                    # dlldir.  To be able to import it without dlldir
                    # being on sys.path, create a loader module and
                    # put that into the archive.
                    pydfile = mod.__name__ + the_extension_target_suffix
                    if self.options.verbose > 1:
                        print("Add Loader for %s to %s" % (os.path.basename(mod.__file__), libpath))
                    loader = py2exe.runtime.LOAD_FROM_DIR.format(pydfile)

                    code = compile(loader, "<loader>", "exec",
                                   optimize=self.options.optimize)
                    if hasattr(mod, "__path__"):
                        path = mod.__name__.replace(".", "\\") + "\\__init__" + bytecode_suffix
                    else:
                        path = mod.__name__.replace(".", "\\") + bytecode_suffix
                    stream = io.BytesIO()
                    stream.write(imp.get_magic())
                    if sys.version_info >= (3,7,0):
                        stream.write(b"\0\0\0\0") # null flags
                    stream.write(b"\0\0\0\0") # null timestamp
                    stream.write(b"\0\0\0\0") # null size
                    marshal.dump(code, stream)
                    arc.writestr(path, stream.getvalue())

        if self.options.bundle_files == 0:
            # put everything into the arc
            files = self.mf.all_dlls()
        elif self.options.bundle_files in (1, 2):
            # put only extension dlls into the arc
            files = self.mf.extension_dlls()
        else:
            arc.close()
            return

        for src in files:
            if self.options.verbose > 1:
                print("Add DLL %s to %s" % (os.path.basename(src), libpath))
            arc.write(src, os.path.basename(src))

        arc.close()

    def copy_files(self, destdir):
        """Copy files (pyds, dlls, depending on the bundle_files value,
        into the dist resp. library directory.
        """
        if self.options.libname is not None:
            libdir = os.path.join(destdir, os.path.dirname(self.options.libname))
        else:
            libdir = destdir

        if self.options.bundle_files >= 2:
            # Python dll is not bundled; copy it into destdir
            dst = os.path.join(destdir, os.path.basename(pydll))
            if self.options.verbose:
                print("Copy %s to %s" % (pydll, destdir))
            shutil.copy2(pydll, dst)
#             with UpdateResources(dst, delete_existing=False) as resource:
#                 resource.add_string(1000, "py2exe")

        if self.options.bundle_files == 3:
            # copy extension modules; they go to libdir
            for mod in self.mf.modules.values():
                if mod.__code__:
                    # nothing to do for python modules.
                    continue
                if hasattr(mod, "__file__"):
                    the_extension_target_suffix = None
                    for ext in EXTENSION_SUFFIXES:
                        if mod.__file__.endswith(ext):
                            the_extension_target_suffix = ext
                            break
                    if the_extension_target_suffix is None:
                        raise RuntimeError(f"Module {mod.__file__} has unknown suffix, not in {EXTENSION_SUFFIXES!r}")
                    pydfile = mod.__name__ + the_extension_target_suffix

                    dst = os.path.join(libdir, pydfile)
                    if self.options.verbose:
                        print("Copy %s to %s" % (mod.__file__, dst))
                    shutil.copy2(mod.__file__, dst)

        if self.options.bundle_files < 1:
            return

        for src in self.mf.real_dlls():
            # Strange, but was tested with numpy built with
            # libiomp5md.dll...
            if self.options.bundle_files == 3:
                extdlldir = libdir
            else:
                extdlldir = destdir
            if self.options.verbose:
                print("Copy DLL %s to %s" % (src, extdlldir))
            shutil.copy2(src, extdlldir)

        # lib files from modulefinder
        for name, src in self.mf._lib_files.items():
            if self.options.bundle_files == 3:
                extdlldir = libdir
            else:
                extdlldir = destdir            
            dst = os.path.join(extdlldir, name)
            # extdlldir can point to a subfolder if it was defined from the `zipfile` option
            if os.path.dirname(extdlldir):
                os.makedirs(os.path.dirname(extdlldir), exist_ok=True)
            else:
                os.makedirs(extdlldir, exist_ok=True)
            if self.options.verbose:
                print("Copy lib file %s to %s" % (src, extdlldir))
            shutil.copy2(src, dst)

        if self.options.bundle_files == 3:
            # extension dlls go to libdir
            for src in self.mf.extension_dlls():
                if self.options.verbose:
                    print("Copy ExtensionDLL %s to %s" % (src, libdir))
                shutil.copy2(src, libdir)

py2exe.runtime.Runtime = Runtime
