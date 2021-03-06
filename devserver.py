from __future__ import absolute_import
import sys
import os
import io
import logging.config

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


def main():
    print(sys.path)
    app_dir = os.path.dirname(sys.executable)
    print(app_dir)
    paths = [app_dir]
    print(paths)
    addsitedir(os.path.join(app_dir, 'site-packages'))
    print(sys.path)
    sys.path[0:0] = paths
    print(sys.path)

    from paste.deploy import loadapp
    from paste.httpserver import serve

    import cryptography.hazmat.primitives.asymmetric.rsa  # noqa
    import cryptography.hazmat.bindings.openssl.binding  # noqa
    logging.config.fileConfig('development.ini')
    app = loadapp('config:development.ini', 'main', relative_to=os.getcwd(), global_conf={})
    server = serve(app, port=8765, start_loop=False)
    print('starting server')
    server.serve_forever()


if __name__ == '__main__':
    main()
