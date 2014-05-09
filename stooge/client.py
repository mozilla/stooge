# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/


import datetime
import random

from celery.execute import send_task
from pymongo import MongoClient
from bson.objectid import ObjectId

from stooge.scanner.celery import celery
from stooge.scanner.tasks import start_scan, finish_scan, execute_scan


def scan(tags=None, random_selection=False):

    client = MongoClient()
    db = client.stooge

    scan_tags = tags if tags is not None else []

    scan = {"tags": scan_tags,
            "created": datetime.datetime.utcnow(),
            "state": "CREATED",
            "started": None,
            "finished": None,
            "sites": []}

    sites = list(db.sites.find())
    if random_selection:
        random.shuffle(sites)
        sites = sites[:10]

    for site in sites:
        scan["sites"].append({"_id": site["_id"],
                              "responses": {"http":[], "https":[]},
                              "results": {},
                              "ssllabs": None,
                              "error": None,
                              "url": site["url"],
                              "bugs": None})

    scan_id = db.scans.insert(scan)

    send_task("stooge.scanner.tasks.execute_scan", [str(scan_id)])
