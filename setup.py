from __future__ import absolute_import
import os
import sys
import fnmatch
from collections import defaultdict
from setuptools import setup, find_packages
import six

version = "1.1.3"

try:
    # py2exe 0.6.4 introduced a replacement modulefinder.
    # This means we have to add package paths there, not to the built-in
    # one.  If this new modulefinder gets integrated into Python, then
    # we might be able to revert this some day.
    # if this doesn't work, try import modulefinder
    try:
        import py2exe.mf as modulefinder
    except ImportError:
        import modulefinder  # noqa
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell"]:  # ,"win32com.mapi"
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
    import pkg_resources
    for p in pkg_resources.__path__[1:]:
        modulefinder.AddPackagePath("pkg_resources", p)
    for extra in ["pkg_resources.extern.packaging", 'pkg_resources.extern.six', 'pkg_resources.extern.six.moves']:
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
except ImportError:
    # no build path setup, no worries.
    pass

if 'py2exe' in sys.argv:
    import py2exe  # noqa
    import compileall

    compileall.compile_dir("offlinetools", force=1)

from distutils.sysconfig import get_python_lib

def find_data_files(source, target, patterns=None):
    """Locates the specified data-files and returns the matches
    in a data_files compatible format.

    source is the root of the source data tree.
        Use '' or '.' for current directory.
    target is the root of the target data tree.
        Use '' or '.' for the distribution directory.
    patterns is a sequence of glob-patterns for the
        files you want to copy.
    """

    if isinstance(patterns, six.string_types):
        patterns = [patterns]
    ret = defaultdict(list)
    for root, dir, filenames in os.walk(source):
        newroot = os.path.join(target, root[len(source) + 1:])
        if patterns:
            filenames = {y for x in patterns for y in fnmatch.filter(filenames, x)}

        ret[newroot].extend(sorted(os.path.join(root, x) for x in filenames))

    ret = list(ret.items())
    ret.sort()
    return ret


class Target(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = version
        self.company_name = "Community Information Online Consortium"
        self.copyright = "Copyright 2011 Community Information Online Consortium"
        self.name = "CIOC Offline Tools Service"

service_definition = Target(
    # used for the versioninfo resource
    description="CIOC Offline Tools Service",
    # what to build.  For a service, the module name (not the
    # filename) must be specified!
    modules=["wsgisvc"],
    cmdline_style='pywin32'

)

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid==1.4.9',
    'SQLAlchemy',
    'transaction',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'zope.sqlalchemy',
    'formencode',
    'paste',
    'pyramid_beaker',
    'requests',
    'backports.ssl_match_hostname',
    'PyCrypto',
    'webhelpers2',
    'pyramid_simpleform',
    'pyramid_exclog',
    'Babel',
    'wincertstore',

    ]

if sys.version_info[:3] < (2, 5, 0):
    requires.append('pysqlite')

setup(
    name='OfflineTools',
    version=version,
    description='CIOC Offline Tools',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='',
    author_email='',
    url='',
    keywords='web wsgi bfg pylons pyramid',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    #test_suite='offlinetools',
    install_requires=requires,
    entry_points="""\
    [paste.app_factory]
    main = offlinetools:main
    """,
    paster_plugins=['pyramid'],
    options={
        'py2exe': {
            'compressed': 1,
            'bundle_files': 2,
            'includes': [
                'dumbdbm', 'anydbm', 'sqlite3', 'new', 'HTMLParser', 'Queue',
                'BaseHTTPServer', 'urllib2', 'cgi', 'io', 'shutil', 'decimal',
                'Cookie', 'win32com.shell.shell', 'win32com.shell.shellcon',
                'xml.etree.cElementTree', 'xml.etree.ElementTree',
                'collections', 'pkgutil', 'symbol', 'distutils'
            ],
            'excludes': [
                "pywin", "pywin.debugger", "pywin.debugger.dbgcon",
                "pywin.dialogs", "pywin.dialogs.list",
                "Tkconstants", "Tkinter", "tcl", 'pkg_resources',
            ],
            'dll_excludes': [
                'POWRPROF.dll', 'API-MS-Win-Core-LocalRegistry-L1-1-0.dll',
                'API-MS-Win-Core-ProcessThreads-L1-1-0.dll',
                'API-MS-Win-Security-Base-L1-1-0.dll'
            ]
        }
    },
    service=[service_definition],
    data_files=(
        find_data_files('offlinetools', 'offlinetools', ['*.pyc', '*.mak']) +
        find_data_files(r'offlinetools\locale', 'offlinetools\locale', '*.mo') +
        find_data_files(r'offlinetools\static', 'offlinetools\static') +
        find_data_files('OfflineTools.egg-info', 'OfflineTools.egg-info') +
        find_data_files(get_python_lib(), 'site-packages')
    )
)
