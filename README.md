<!--
    This file is auto generated by the GRAND framework.
    Beware: any change to this file will be overwritten at next commit.
    One should edit the docs/README.md file instead.
-->

[![PyPi version](https://img.shields.io/pypi/v/g.svg)](https://pypi.org/project/grand-framework)
[![Coding style](https://img.shields.io/badge/pep8-85%25-brightgreen.svg)](https://github.com/grand-mother/framework/blob/master/docs/.stats.json)
[![Code coverage](https://codecov.io/gh/grand-mother/framework/branch/master/graph/badge.svg)](https://codecov.io/gh/grand-mother/framework)
[![Build status](https://travis-ci.com/grand-mother/framework.svg?branch=master)](https://travis-ci.com/grand-mother/framework)

# Framework
_Common framework for GRAND packages_


## Description

This is a utility for managing and distributing GRAND packages within a common
_standard_ framework. It provides:

- An encapsulation of `setuptools` for building a version controlled package
  that includes GRAND meta data.

- Continuous Integration (CI) tests, both locally, with git hooks, and
  via [GitHub][GITHUB].

- ~~An automatic documentation generation~~, well ... soon it should.

This utility ships with an executable, `grand-pkg-init`, which allows to create
or convert an existing GRAND package, as:
```bash
grand-pkg-init path/to/package
```
Then, you might need to answer a few questions in order to configure the GRAND
package.


## Installation

The latest stable version of this package can be installed from [PyPi][PYPI]
using [pip][PIP], e.g. as:
```bash
pip install --user grand-framework
```

Alternatively one can also install the latest development commit directly from
[GitHub][GITHUB], as:
```bash
pip install --user git+https://github.com/grand-mother/framework.git@master
```


## License

The GRAND software is distributed under the LGPL-3.0 license. See the provided
[`LICENSE`][LICENSE] and [`COPYING.LESSER`][COPYING] files.


[COPYING]: https://github.com/grand-mother/framework/blob/master/COPYING.LESSER
[GITHUB]: https://github.com/grand-mother/framework
[LICENSE]: https://github.com/grand-mother/framework/blob/master/LICENSE
[PIP]: https://pypi.org/project/pip
[PYPI]: https://pypi.org/project/grand-framework
