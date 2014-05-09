# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

import urlparse
import stooge.curly as curly

# Utils

def final_response(http_responses, https_responses):
    if https_responses:
        return https_responses[-1]
    else:
        return http_responses[-1]

def is_http(response):
    return response["url"].startswith("http://")

def is_https(response):
    return response["url"].startswith("https://")

def get_result(results, category, check):
    for r in results.get(category,[]):
        if r["name"] == check:
            return r["result"]

# Basic checks

def ssl(site, results, http_responses, https_responses):
    r = final_response(http_responses, https_responses)
    return is_https(r)

def xfo(site, results, http_responses, https_responses):
    r = final_response(http_responses, https_responses)
    return "x-frame-options" in r["headers"]

def server(site, results, http_responses, https_responses):
    for r in http_responses:
        if "server" in r["headers"] and "/" in r["headers"]["server"]:
            return False
        if "x-powered-by" in r["headers"]:
            return False
    for r in https_responses:
        if "server" in r["headers"] and "/" in r["headers"]["server"]:
            return False
        if "x-powered-by" in r["headers"]:
            return False
    return True

def xxp(site, results, http_responses, https_responses):
    r = final_response(http_responses, https_responses)
    return "x-xss-protection" in r["headers"]

def xcto(site, results, http_responses, https_responses):
    r = final_response(http_responses, https_responses)
    return "x-content-type-options" in r["headers"]

# CSP Checks

def csp_present(site, results, http_responses, https_responses):
    r = final_response(http_responses, https_responses)
    return "content-security-policy" in r["headers"]

def cspro_present(site, results, http_responses, https_responses):
    r = final_response(http_responses, https_responses)
    if "content-security-policy-report-only" in r["headers"]:
        return True

def csp_valid(site, results, http_responses, https_responses):
    if get_result(results, "csp", "csp_present"):
        return True # TODO

def cspro_valid(site, results, http_responses, https_responses):
    if get_result(results, "csp", "cspro_present"):
        return True # TODO

# SSL Checks

def ssl_present(site, results, http_responses, https_responses):
    return is_https(http_responses[-1]) or len(https_responses) != 0

def ssl_grade(site, results, http_responses, https_responses):
    if get_result(results, "ssl", "ssl_present") and site["ssllabs"]:
        return site["ssllabs"]["endpoints"][0]["grade"]

def ssl_pfs(site, results, http_responses, https_responses):
    if get_result(results, "ssl", "ssl_present") and site["ssllabs"]:
        return site["ssllabs"]["endpoints"][0]["results"]["details"]["forwardSecrecy"]

def ssl_heartbleed(site, results, http_responses, https_responses):
    if get_result(results, "ssl", "ssl_present") and site["ssllabs"]:
        return not site["ssllabs"]["endpoints"][0]["results"]["details"]["heartbleed"]

def sslredirect(site, results, http_responses, https_responses):
    if get_result(results, "ssl", "ssl_present"):
        first_response = http_responses[0]
        final_response = http_responses[-1]
        return is_http(first_response) and is_https(final_response)

def hsts(site, results, http_responses, https_responses):
    if get_result(results, "ssl", "ssl_present"):
        r = final_response(http_responses, https_responses)
        if is_https(r):
            return "strict-transport-security" in r["headers"]

#

BASIC_CHECKS = [
    xfo,
    xxp,
    xcto,
    server,
]

CSP_CHECKS = [
    csp_present,
    csp_valid,
    cspro_present,
    cspro_valid,
]

SSL_CHECKS = [
    ssl_present,
    ssl_grade,
    hsts,
    sslredirect,
]

def execute_checks_against_responses(site):
    results = {"basic":[], "csp":[], "ssl":[]}
    for check in BASIC_CHECKS:
        results["basic"].append({"name": check.__name__, "result": check(site, results, site["responses"]["http"], site["responses"]["https"])})
    for check in CSP_CHECKS:
        results["csp"].append({"name": check.__name__, "result": check(site, results, site["responses"]["http"], site["responses"]["https"])})
    for check in SSL_CHECKS:
        results["ssl"].append({"name": check.__name__, "result": check(site, results, site["responses"]["http"], site["responses"]["https"])})
    return results
