# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

import os
import subprocess
import json

def analyze(target, path="/usr/local/cipherscan"):
    os.chdir(path)
    results = subprocess.check_output(["./analyze.py", "-t", target, "-j"])
    return json.loads(results)
