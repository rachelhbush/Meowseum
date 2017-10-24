from os import listdir
from os.path import dirname, basename, isfile, splitext, join
# Get a list of directories and file names with extensions in this file's directory.
modules = listdir(dirname(__file__))
# For each item, filter down to only files, aside from this file, and remove the extension.
__all__ = [ splitext(f)[0] for f in modules if isfile(join(dirname(__file__), f)) and not f.endswith('__init__.py')]
