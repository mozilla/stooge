# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

from __future__ import absolute_import

import datetime
import os
import time
import urlparse
import sys

import requests
from celery.utils.log import get_task_logger
from celery.execute import send_task
from celery import chain, group
from pymongo import MongoClient
from bson.objectid import ObjectId

from stooge.scanner.celery import celery
from stooge.scanner.checks import execute_checks_against_responses, get_result, final_response, is_https
import stooge.curly as curly
import stooge.scanner.ssllabs as ssllabs
from boogs import BugBuilder

#

sys.setrecursionlimit(10000) # To overcome some silly Celery issue with long chains

#

client = MongoClient()
db = client.stooge
scans = db.scans

#

logger = get_task_logger(__name__)

#

def find_site(scan, site_id):
    for site in scan["sites"]:
        if ObjectId(site["_id"]) == ObjectId(site_id):
            return site

#

@celery.task
def site_task(scan_id, site_id):

    logger.info("Loading site %s" % site_id)

    try:

        scan = scans.find_one({"_id": ObjectId(scan_id)})
        if not scan:
            logger.error("Cannot load scan %s" % scan_id)
            return

        site = find_site(scan, site_id)
        if not site:
            logger.error("Cannot find site in scan")
            return

        responses = {"http":[], "https":[]}

        # Grab the HTTP responses

        r = curly.get(site["url"])
        for response in r.history:
            responses["http"].append({"status": response.status, "headers": response.headers, "url": response.url})

        # Grab the HTTPS responses, may fail if the site does not support HTTPS

        final_http_response = responses["http"][-1]
        if final_http_response["url"].startswith("http://"):
            try:
                url = urlparse.urlparse(site["url"])
                r = curly.get("https://%s" % url.hostname)
                for response in r.history:
                    responses["https"].append({"status": response.status, "headers": response.headers, "url": response.url})
            except Exception as e:
                logger.exception("Error while trying https request")
                # TODO We probably want to check if the exception is connectionrefused or timeout

        # Store the responses

        scans.update({"_id": ObjectId(scan_id), "sites._id": ObjectId(site_id)},
                     {"$set": {"sites.$.responses": responses}})

    except Exception as e:

        logger.exception("Error while scanning site")

        try:
            scans.update({"_id": ObjectId(scan_id), "sites._id": ObjectId(site_id)},
                         {"$set": {"sites.$.results": None,
                                   "sites.$.error": str(e)}})
        except Exception as e:
            logger.exception("Error when marking site as failed")

#

@celery.task
def check_task(scan_id, site_id):

    logger.info("Checking site %s" % site_id)

    try:

        scan = scans.find_one({"_id": ObjectId(scan_id)})
        if not scan:
            logger.error("Cannot load scan %s" % scan_id)
            return

        site = find_site(scan, site_id)
        if not site:
            logger.error("Cannot find site in scan")
            return

        # Execute our checks

        try:
            results = execute_checks_against_responses(site)
            scans.update({"_id": ObjectId(scan_id), "sites._id": ObjectId(site_id)},
                         {"$set": {"sites.$.results": results}})
        except Exception as e:
            logger.exception("Error while executing checks")

    except Exception as e:

        logger.exception("Error while checking site")

        try:
            scans.update({"_id": ObjectId(scan_id), "sites._id": ObjectId(site_id)},
                         {"$set": {"sites.$.results": None,
                                   "sites.$.error": str(e)}})
        except Exception as e:
            logger.exception("Error when marking site as failed")

#

def count_websec_bugs(bugzilla_username, bugzilla_password, site_url):

    url = urlparse.urlparse(site_url)

    def _websec_bugs_via_component(credentials, site):
        bb = BugBuilder(credentials=credentials)
        bb.product("Websites")
        bb.component(site)
        bb.fields("id", "creation_time", "status", "summary", "assigned_to")
        bb.open()
        bb.advanced("bug_group", "equals", "websites-security")
        req = bb.build()
        r = requests.get(req.url, params=req.params, headers=req.headers)
        return r.json().get("bugs", [])

    def _websec_bugs_via_whiteboard(credentials, site):
        bb = BugBuilder(credentials=credentials)
        #bb.product("Websites")
        bb.fields("id", "creation_time", "status", "summary", "assigned_to")
        bb.open()
        bb.advanced("status_whiteboard", "substring", "[site:%s]" % site)
        req = bb.build()
        r = requests.get(req.url, params=req.params, headers=req.headers)
        return r.json().get("bugs", [])

    credentials = (bugzilla_username, bugzilla_password)

    bug_ids = set()
    bug_ids.add([bug['id'] for bug in _websec_bugs_via_component(credentials, url.hostname)])
    bug_ids.add([bug['id'] for bug in _websec_bugs_via_whiteboard(credentials, url.hostname)])

    return len(bug_ids)

@celery.task
def bugcount_task(scan_id, site_id):

    bugzilla_username = os.getenv("BUGZILLA_USERNAME")
    bugzilla_password = os.getenv("BUGZILLA_PASSWORD")

    if not bugzilla_username or not bugzilla_password:
        return

    logger.info("Counting websec bugs for site %s" % site_id)

    try:

        scan = scans.find_one({"_id": ObjectId(scan_id)})
        if not scan:
            logger.error("Cannot load scan %s" % scan_id)
            return

        site = find_site(scan, site_id)
        if not site:
            logger.error("Cannot find site in scan")
            return

        n = count_websec_bugs(bugzilla_username, bugzilla_password, site["url"])

        scans.update({"_id": ObjectId(scan_id), "sites._id": ObjectId(site_id)},
                     {"$set": {"sites.$.bugs": n}})

    except Exception as e:

        logger.exception("Error while counting websec bugs")

@celery.task
def ssllabs_task(scan_id, site_id):

    logger.info("Counting websec bugs for site %s" % site_id)

    try:

        scan = scans.find_one({"_id": ObjectId(scan_id)})
        if not scan:
            logger.error("Cannot load scan %s" % scan_id)
            return

        site = find_site(scan, site_id)
        if not site:
            logger.error("Cannot find site in scan")
            return

        r = final_response(site["responses"]["http"], site["responses"]["https"])
        if is_https(r):

            url = urlparse.urlparse(site["url"])
            logger.info("Going to check %s with ssllabs" % url.hostname)

            try:
                results = ssllabs.assess_site(url.hostname)
                scans.update({"_id": ObjectId(scan_id), "sites._id": ObjectId(site_id)},
                             {"$set": {"sites.$.ssllabs": results}})
            except Exception as e:
                logger.exception("Error while talking to ssllabs")

    except Exception as e:

        logger.exception("Error while running ssllabs_task")

#

@celery.task(ignore_result=True)
def start_scan(scan_id):

    logger.info("start_scan")

    scans.update({"_id": ObjectId(scan_id)},
                 {"$set": {"state": "STARTED",
                           "started": datetime.datetime.utcnow()}})

@celery.task(ignore_result=True)
def finish_scan(scan_id):

    logger.info("finish_scan")

    scans.update({"_id": ObjectId(scan_id)},
                 {"$set": {"state": "FINISHED",
                           "finished": datetime.datetime.utcnow()}})

@celery.task(ignore_result=True)
def execute_scan(scan_id):

    logger.info("execute_scan")

    scan = scans.find_one({"_id": ObjectId(scan_id)})
    if not scan:
        logger.error("Cannot load scan %s" % scan_id)
        return

    # To get results quicker, we interleave all the tasks. So they look like:
    # chain(start_scan, chain(chain(site, ssllabs, check, bugcount), ...), finish_scan)

    site_tasks = [site_task.si(str(scan_id), str(site["_id"])) for site in scan["sites"]]
    ssllabs_tasks = [ssllabs_task.si(str(scan_id), str(site["_id"])) for site in scan["sites"]]
    check_tasks = [check_task.si(str(scan_id), str(site["_id"])) for site in scan["sites"]]
    bugcount_tasks = [bugcount_task.si(str(scan_id), str(site["_id"])) for site in scan["sites"]]

    grouped_tasks = [chain(*i) for i in zip(site_tasks, ssllabs_tasks, check_tasks, bugcount_tasks)]
    chain(start_scan.si(scan_id), chain(*grouped_tasks), finish_scan.si(scan_id))()
