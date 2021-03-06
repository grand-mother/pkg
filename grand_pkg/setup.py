# -*- coding: utf-8 -*-
"""
Encapsulation of setuptools for GRAND

Copyright (C) 2018 The GRAND collaboration

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys

from distutils.core import Command
from setuptools import setup, find_packages
from . import PKG_FILE

try:
    system = subprocess.getoutput
except:
    def system(command):
        p = subprocess.Popen(command, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p.communicate()[0]

__all__ = [ "setup_package" ]


DEFAULT_CLASSIFIERS = """\
Intended Audience :: Science/Research
License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)
Programming Language :: Python :: 3.7
Topic :: Scientific/Engineering
Operating System :: POSIX
Operating System :: POSIX :: Linux
Operating System :: Unix
Operating System :: MacOS
"""
"""Default PyPi classifiers for GRAND packages
"""


_PACKAGE_DIR = "."


def make_version_module(package, version):
    """
    Build the version.py module for the distribution

    ### This is an example of documentation
    **Any** thing could go here. For example as:
    ```c
        int main(int nargc, char * argv[])
        {
            return 0;
        }
    ```
    - But this is ~~not~~.

    Parameters
    ----------
    package : str
        The git package name
    version : str
        The full version tag

    Returns
    -------
    toto : None
        This is nasty
    str
        Guess?

    Yields
    ------

    toto : None
        This is nasty
    str
        Guess?

    Raises
    ------
    RuntimeError
        Never do that again
    FatalMistake
        Try again

    """

    status = system("git status --porcelain")
    if status and not ("pip-delete-this-directory.txt" in str(status)):
        raise RuntimeError("Dirty git status")

    sha1, author, date = map(lambda s: s.strip(), system(
        "git show -s --format='%H|%cn|%ci' HEAD").split("|"))
    count = system("git rev-list --count HEAD").strip()

    content = os.linesep.join((
        "# -*- coding: utf-8 -*-",
        '"""',
        "Autogenerated version and git info",
        "",
        "This module was auto generated by the GRAND package manager",
        "Beware : any change will be overwritten at next build",
        '"""',
        "",
        "__version__ = \"{:}\"",
        "__git__ = {{",
        "    \"sha1\": \"{:}\",",
        "    \"author\": \"{:}\",",
        "    \"date\": \"{:}\",",
        "    \"count\": {:}",
        "}}")).format(version, sha1, author, date, count)

    path = os.path.join(_PACKAGE_DIR, package, "version.py")
    with open(path, "w+") as f:
        f.write(content)

    return sha1


def get_meta():
    """Load the package meta_data"""

    path = os.path.join(_PACKAGE_DIR, PKG_FILE)
    with open(path, "r") as f:
        pkg_data = json.load(f)["package"]

    meta = {"name": pkg_data["dist-name"],
            "description": pkg_data["description"]}

    return pkg_data["name"], pkg_data["git-name"], meta


class DistClean(Command):
    """Custom clean command, to really clean the repo"""

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Remove build and dist data
        def remove_directory(dirname):
            path = os.path.join(_PACKAGE_DIR, dirname)
            if os.path.exists(path):
                print("removing " + dirname)
                shutil.rmtree(path, ignore_errors=True)

        remove_directory("build")
        remove_directory("dist")
        remove_directory("__pycache__")
        for path in glob.glob("*.egg-info"):
            remove_directory(path)

        # Remove bytecode and version module
        packages = find_packages(_PACKAGE_DIR)
        for package in packages:
            source_dir = os.path.join(_PACKAGE_DIR, package)
            print("cleaning " + package + " source")

            path = os.path.join(source_dir, "__pycache__")
            shutil.rmtree(path, ignore_errors=True)

            path = os.path.join(source_dir, "version.py")
            if os.path.exists(path):
                os.remove(path)

            for root, _, files in os.walk(source_dir):
                for file_ in files:
                    _, ext = os.path.splitext(file_)
                    if ext in (".pyc", ".pyo"):
                        path = os.path.join(root, file_)
                        os.remove(path)

        for ext in ("*.pyc", "*.pyo"):
            pattern = os.path.join(_PACKAGE_DIR, ext)
            for file_ in glob.glob(pattern):
                os.remove(file_)


def setup_package(file_, numeric_version, extra_classifiers=None, **kwargs):
    """Wrapper of the distutils.setup function, for GRAND packages"""

    # Check the setup command
    try:
        command = sys.argv[1]
    except IndexError:
        setup()

    clean = (command == "clean") or (command == "distclean")

    # Export the root directory of the package
    global _PACKAGE_DIR
    _PACKAGE_DIR = os.path.abspath(os.path.dirname(file_))

    # Format the version string
    version = "{:d}.{:d}.{:d}".format(*numeric_version)

    # Get the package meta data
    package_name, git_name, meta = get_meta()

    if not clean:
        # Make the version module. Note that this will check the git
        # status as Well
        sha1 = make_version_module(package_name, version)

    # Merge the classifiers
    all_classifiers = [s for s in DEFAULT_CLASSIFIERS.splitlines() if s]
    if extra_classifiers is not None:
        all_classifiers += extra_classifiers

    # Load the description
    with open(os.path.join(_PACKAGE_DIR, "README.md")) as f:
        long_description = f.read()

    if not clean:
        # Prune the doc for PyPI
        img = "https://img.shields.io/badge/GitHub-{:}-blue.svg".format(
            sha1[:7])
        url = "https://github.com/grand-mother/{:}/tree/{:}".format(
            git_name, sha1)
        badge = "[![GitHub hash]({:})]({:})".format(img, url)
        long_description = re.sub("\[!\[PyPi version\].*", badge,
                                  long_description)

    # Extra package meta data
    meta.update(dict(
        # The maintainer(s) of the package, i.e. those who publish it
        maintainer = "GRAND Developers",
        maintainer_email = "grand-dev@googlegroups.com",

        # The package description
        version = version,
        url = "https://github.com/grand-mother/" + git_name,
        packages = find_packages(_PACKAGE_DIR, exclude=("tests",)),
        long_description = long_description,
        long_description_content_type = "text/markdown",
        include_package_data = True,
        classifiers = all_classifiers,

        # Custom clean command
        cmdclass = { "distclean" : DistClean },

        # The tests suite is explicitly given, to prevent a detailed inspection
        # of the package by the tests discovery tools
        test_suite="tests"
    ))

    # User meta data
    meta.update(kwargs)

    # Call the setup tool
    setup(**meta)
