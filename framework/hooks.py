# -*- coding: utf-8 -*-
"""
Git hooks providing local CI

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

import importlib
import inspect
import json
import os
import subprocess
import sys

try:
    from pycodestyle import StyleGuide
except ImportError:
    StyleGuide = None

try:
    from .setup import get_alts, system
except:
    from framework.setup import get_alts, system
try:
    from version import __version__
except ImportError:
    __version__ = "unknown"

__all__ = ["pre_commit", "prepare_commit_msg"]


def git(*args):
    """System git call"""
    command = "git " + " ".join(args)
    return system(command)


def get_top_directory():
    """Get the package top directory from git"""
    top = git("rev-parse", "--show-toplevel")
    return top.strip()


def count_lines_in(file_):
    """Count the number of code lines in a Python file"""

    with open(file_, "r") as f:
        lines = f.readlines()

    docmarker = None
    blank, comment, docstring, code = 4 * (0,)
    for line in lines:
        if docmarker is None:
            if (not line) or (line == os.linesep):
                blank += 1
            elif line[0] == "#":
                comment += 1
            else:
                index = line.find('"""')
                if index >= 0:
                    docmarker = '"""'
                    docstring += 1
                else:
                    index = line.find("'''")
                    if index >= 0:
                        docmarker = "'''"
                        docstring += 1
                if index == -1:
                    # This isn't a docstring neither, so it must be
                    # code finally
                    code += 1
                else:
                    index = line[index+3:].find(docmarker)
                    if index >= 0:
                        # This is a 1 line docstring
                        docmarker = None
        else:
            docstring += 1
            if docmarker in line:
                docmarker = None

    return blank, comment, docstring, code 


def count_lines(path):
    """Count the number of Python code lines, recursively"""

    def format(counts):
        return {"blank": counts[0], "comment": counts[1],
                "docstring": counts[2], "code": counts[3]}

    _, ext = os.path.splitext(path)
    if ext == ".py":
        return format(count_lines_in(path))

    counts = 4 * [0,]
    for root, dirs, files in os.walk(path):
        for file_ in files:
            _, ext = os.path.splitext(file_)
            if ext == ".py":
                c = count_lines_in(os.path.join(root, file_))
                for i, ci in enumerate(c):
                    counts[i] += ci
    return format(counts)


def check_style(path):
    """Check the conformity to PEP8"""

    if StyleGuide is not None:
        style_guide = StyleGuide(quiet=True)
        report = style_guide.check_files(paths=(path,))
        stats = [line.split(None, 2) for line in report.get_statistics()]
        return { "count": report.get_count(), "categories": stats }
    else:
        return { "count": None, "categories": None }

def gather_doc(package_dir, package_name):
    """Gather public objects and their associated docstrings"""

    def gather(obj):
        """Gather info recursively"""
        modules, classes, functions = {}, {}, {}
        for name, data in inspect.getmembers(obj):
            if name.startswith("_"):
                continue

            # Check the object type
            if inspect.isclass(data):
                container, attr = classes, "__module__"
            elif inspect.isfunction(data):
                container, attr = functions, "__module__"
            elif inspect.ismodule(data) and (name != "version"):
                container, attr = modules, "__package__"
            else:
                continue

            source = getattr(data, attr)
            if ((source != package_name) and not
                (source.startswith(package_name + "."))):
                continue

            # Gather the doc for this object
            file_ = inspect.getsourcefile(data).split(package_name + "/")[-1]
            _, lineno = inspect.getsourcelines(data)
            doc = inspect.getdoc(data)
            if doc is not None:
                doc = doc.split(
                    "\n\nCopyright (C) 2018 The GRAND collaboration",1)[0]
                doc = inspect.cleandoc(doc)

            if container is modules:
                info = (file_, lineno, doc, gather(data)) 
            else:
                info = (file_, lineno, doc)

            container[name] = info 

        return {"classes": classes, "functions": functions, "modules": modules}

    # Import the package
    sys.path.append(package_dir)
    package = importlib.import_module(package_name)

    # Gather the doc and return
    return gather(package)

def analyse_package(package_dir, package_name):
    """Analyse the content of a package and dump statistics"""

    path = os.path.join(package_dir, package_name)
    stats = {}
    stats["lines"] = count_lines(path)
    stats["pep8"] = check_style(path)
    stats["doc"] = gather_doc(package_dir, package_name)

    path = os.path.join(package_dir, ".stats.json")
    with open(path, "w") as f:
        json.dump(stats, f)

    git("add", path)

    return stats


def update_readme(package_dir, package_name, stats, readme):
    """Update the package README"""
    preamble = [
"""\
<!--
    This file is auto generated by the GRAND framework.
    Beware: any change to this file will be overwritten at next commit.
    One should edit the docs/README.md file instead.
-->
"""]

    def add_badge(alt, link, pattern, image=None, shield=None):
        if shield:
            img = "https://img.shields.io/" + pattern.format(*shield)
        elif image:
            img = pattern.format(*image)
        else:
            img = pattern
        badge = "[![{:}]({:})]({:})".format(alt, img, link)
        preamble.append(badge)

    def colormap(score):
        colors = ("red", "orange", "yellow", "yellowgreen", "green",
                  "brightgreen")
        n = len(colors)
        index = int(n * score * 1E-02)
        index = min(n - 1, index)
        index = max(0, index)
        return colors[index]

    # PEP8 badge
    git_name, dist_name = get_alts(package_name)
    lines = stats["lines"]["code"]
    score = int(100. * (lines - stats["pep8"]["count"]) / float(lines))
    color = colormap(score)
    add_badge(
        "Coding style",
        "https://github.com/grand-mother/" + git_name +
            "/blob/master/docs/.stats.json",
        "badge/pep8-{:}%25-{:}.svg", shield=(score, color))

    # Coverage badge
    base_url = "https://codecov.io/gh/grand-mother/"
    add_badge(
        "Code coverage",
        base_url + git_name,
        "{:}{:}/branch/master/graph/badge.svg", image=(base_url, git_name))

    # Travis badge
    base_url = "https://travis-ci.com/grand-mother/"  
    add_badge(
        "Build status",
        base_url + git_name,
        "{:}{:}.svg?branch=master", image=(base_url, git_name))

    # PyPi badge
    add_badge(
        "PyPi version",
        "https://pypi.org/project/" + dist_name,
        "pypi/v/{:}.svg", shield=dist_name)

    path = os.path.join(package_dir, "README.md")
    with open(path, "w") as f:
        f.write(os.linesep.join(preamble))
        f.write(2 * os.linesep)
        f.write(readme)

    git("add", path)


def add_banner(msg):
    """Add a banner to git commit messages"""

    try:
        head, tail = msg.split("#", 1)
    except ValueError:
        return msg

    return """{:}\
# =================================================================
#      This commit has been analysed by grand-framework {:}
# =================================================================
#{:}
""".format(head, __version__, tail)


def pre_commit():
    """Git hook for pre-processing a commit"""

    package_dir = get_top_directory()
    path = os.path.join(package_dir, "docs", "README.md")
    with open(path, "r") as f:
        readme = f.read()

    # Parse the package name from the docs/README
    tail = readme
    while tail:
        line, tail = tail.split(os.linesep, 1) 
        if line and (line[0] == "#"):
            package_name = line[1:].strip().lower().replace(" ", "_")
            break

    # Compute the stats
    stats = analyse_package(package_dir, package_name)

    # Update the package README
    update_readme(package_dir, package_name, stats, readme)
    sys.exit(0)


def prepare_commit_msg(file_=None):
    """Git hook for preparing the commit message"""
    if file_ is None:
        file_ = sys.argv[1]
    with open(file_, "r") as f:
        initial_msg = f.read()

    msg = add_banner(initial_msg)

    if msg is not initial_msg:
        with open(file_, "w") as f:
            f.write(msg)
    sys.exit(0)


if __name__ == "__main__":
    # Get the function to call from the command line
    ret = globals()[sys.argv[1]](*sys.argv[2:])
    if ret is not None:
        print(ret)
