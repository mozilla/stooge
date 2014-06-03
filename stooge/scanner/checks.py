# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

import urlparse
import stooge.curly as curly
import csp_validator.csp

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

def csp_valid(site, results, http_responses, https_responses):
    if get_result(results, "csp", "csp_present"):
        r = final_response(http_responses, https_responses)
        parsed_csp = csp_validator.csp.validate(r["headers"]["content-security-policy"])
        return parsed_csp['valid']

def csp_reports(site, results, http_responses, https_responses):
    if get_result(results, "csp", "csp_valid"):
        r = final_response(http_responses, https_responses)
        policy = csp_validator.csp.parse_policy(r["headers"]["content-security-policy"])
        return 'report-uri' in policy

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
    csp_reports
]

SSL_CHECKS = [
    ssl_present,
    ssl_grade,
    hsts,
    sslredirect,
]

def execute_checks_against_responses(site):
    results = {"basic":[], "csp":[], "ssl":[]}
    if site.get("error") is None:
        for check in BASIC_CHECKS:
            results["basic"].append({"name": check.__name__,
                                     "result": check(site, results, site["responses"]["http"], site["responses"]["https"])})
        for check in CSP_CHECKS:
            results["csp"].append({"name": check.__name__,
                                   "result": check(site, results, site["responses"]["http"], site["responses"]["https"])})
        for check in SSL_CHECKS:
            results["ssl"].append({"name": check.__name__,
                                   "result": check(site, results, site["responses"]["http"], site["responses"]["https"])})
    return results
