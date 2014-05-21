#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

from setuptools import setup

install_requires = [
    'Flask==0.10.1',
    'requests==2.3.0',
    'celery==3.1.11',
    'pycurl==7.19.3.1',
    'pymongo==2.7',
    'boogs==0.1'
]

setup(name="stooge",
      version="0.1",
      description="Stooge",
      url="https://github.com/st3fan/stooge",
      author="Stefan Arentz",
      author_email="sarentz@mozilla.com",
      install_requires = install_requires,
      packages=["stooge", "stooge.scanner"],
      scripts=["scripts/stooge-web", "scripts/stooge-scanner", "scripts/stooge-ctl"])
