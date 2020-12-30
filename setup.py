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
import sys
import shutil
import fnmatch
from collections import defaultdict
from setuptools import setup, find_packages
import six

version = "2.0.1"

if 'py2exe' in sys.argv:
    # this monkeypatches out the issue from https://github.com/py2exe/py2exe/issues/32
    import py2exeruntimepatch  # noqa
    #import py2exe  # noqa
    import compileall

    compileall.compile_dir("offlinetools", force=1)

from distutils.sysconfig import get_python_lib

cleaned_run = False


def copy_and_find_data_files(source, target, patterns=None):
    global cleaned_run
    if not cleaned_run:
        # clear our copied values for new run
        cleaned_run = True
        shutil.rmtree('build/tmp', True)
        # ensure that target directory exists
        os.makedirs('build/tmp', )

    tmp_src = 'build/tmp/' + os.path.basename(source)
    shutil.copytree(source, tmp_src)
    return find_data_files(tmp_src, target, patterns)


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
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid==1.5.8',
    'SQLAlchemy',
    'transaction',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'zope.sqlalchemy',
    'FormEncode',
    'paste',
    'pyramid_beaker',
    'requests',
    'cryptography',
    'webhelpers2',
    'pyramid_simpleform',
    'pyramid_exclog',
    'Babel',
    'wincertstore',
    ]

data_files = (
)

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
    # test_suite='offlinetools',
    install_requires=requires,
    entry_points="""\
    [paste.app_factory]
    main = offlinetools:main
    """,
    paster_plugins=['pyramid'],
    options={
        'py2exe': {
            # 'skip_archive': True,
            'bundle_files': 3,
            'includes': [
                'sqlite3',
                'xml.etree.cElementTree', 'xml.etree.ElementTree',
                'symbol', 'distutils', 'logging.config', 'urllib.request', 'http.cookies',
                'html.parser', 'uuid', 'decimal', 'six', 'cgi', 'dbm', 'timeit', 'ipaddress',
                #'_uuid'
            ],
            'excludes': [
                "pywin", "pywin.debugger", "pywin.debugger.dbgcon",
                "pywin.dialogs", "pywin.dialogs.list",
                "Tkconstants", "Tkinter", "tcl", 'pkg_resources',
            ],
            'dll_excludes': [
            ]
        }
    },
    service=[service_definition],
    console=['devserver.py'],
    data_files=(
        find_data_files('offlinetools', 'offlinetools', ['*.py', '*.pyc', '*.mak']) +
        find_data_files(r'offlinetools\locale', 'offlinetools\locale', ['*.mo']) +
        find_data_files(r'offlinetools\static', 'offlinetools\static') +
        find_data_files('OfflineTools.egg-info', 'OfflineTools.egg-info') +
        copy_and_find_data_files(get_python_lib(), 'site-packages') +
        copy_and_find_data_files('c:/python38/Lib/site-packages/six-1.15.0.dist-info', 'site-packages/six-1.15.0.dist-info') +
        # [('site-packages', [get_python_lib() + '/../site.py', get_python_lib() + '/../orig-prefix.txt'])] +
        [('', ['production.ini', 'development.ini'])]
    )
)
