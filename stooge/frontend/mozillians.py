# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

import requests

def lookup_mozillian(app_name, app_key, email):
    params = dict(app_name=app_name, app_key=app_key, email=email)
    r = requests.get("https://mozillians.org/api/v1/users/", params=params)
    r.raise_for_status()
    objects = r.json()["objects"]
    if objects:
        return objects[0]
