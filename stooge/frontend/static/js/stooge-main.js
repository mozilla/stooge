// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/

// Should this go in a module?

function sortScanSites (e) {
    var url = e.url;
    if (url.indexOf("http://www.") == 0) {
        return url.substring(11);
    } else if (url.indexOf("http://") == 0) {
        return url.substring(7);
    } else if (url.indexOf("https://www.") == 0) {
        return url.substring(12);
    } else if (url.indexOf("https://") == 0) {
        return url.substring(8);
    } else {
        return url;
    }
}

//

var stoogeApp = angular.module("stoogeApp", ['ngRoute', 'stoogeControllers', 'stoogeServices']);

stoogeApp.controller("StoogeController", function($rootScope, $scope, $http, Scan) {
    $http.get('/api/session').
        success(function(response, status, headers, config) {
            $scope.session = response.data;
        });
});

stoogeApp.filter('scanDate', function() {
    return function(input) {
        var m = moment(input);
        return m.format("dddd, MMMM Do YYYY");
    };
});

stoogeApp.filter('testLabelClass', function() {
    return function(result) {
        if (result.name === "ssl_grade") {
            if (result.result === 'A' || result.result === 'A+' || result.result === 'A-') {
                return "ssl-grade-label-success"
            } else if (result.result === 'F') {
                return "ssl-grade-label-important";
            } else if (result.result === null) {
                return "ssl-grade-label-na";
            } else {
                return "ssl-grade-label-warning";
            }
        } else if (result.name === "ssl_pfs") {
            if (result.result === null) {
                return "test-label-na";
            } else if (result.result === 0) {
                return "label-important";
            } else if (result.result === 1) {
                return "label-success";
            } else {
                return "label-warning";
            }
        } else {
            if (result.result === true) {
                return "test-label-pass";
            }
            if (result.result === false) {
                return "test-label-fail";
            }
        }
        return "test-label-na";
    };
});

stoogeApp.filter('prettyTestName', function() {
    return function(result) {
        switch (result.name) {
        case "xfo":
            return "XFO";
        case "sslredirect":
            return "SSLRedirect";
        case "csp_present":
            return "CSP";
        case "csp_valid":
            return "CSP-Valid";
        case "cspro_present":
            return "CSPRO";
        case "cspro_valid":
            return "CSPRO-Valid";
        case "hsts":
            return "HSTS";
        case "server":
            return "Server";
        case "xcto":
            return "XCTO";
        case "xxp":
            return "XXP";
        case "ssl_present":
            return "SSL";
        case "ssl_grade":
            return result.result || "-";
        case "ssl_pfs":
            return "FS";
        case "ssl_heartbleed":
            return "Heartbleed";
        }
        return input;
    };
});

stoogeApp.filter('shortBugStatus', function() {
    return function(status) {
        switch (status) {
        case "UNCONFIRMED":
            return "UNC";
        case "NEW":
            return "NEW";
        case "RESOLVED":
            return "RES";
        case "VERIFIED":
            return "VER";
        case "REOPENED":
            return "REO";
        case "ASSIGNED":
            return "ASS";
        }
        return "UNK";
    };
});

stoogeApp.filter('shortBugStatusLabel', function() {
    return function(status) {
        switch (status) {
        case "UNCONFIRMED":
            return "label-info";
        case "NEW":
            return "label-info";
        case "RESOLVED":
            return "label-default";
        case "VERIFIED":
            return "label-default";
        case "REOPENED":
            return "label-info";
        case "ASSIGNED":
            return "label-info";
        }
        return "label-default";
    };
});

stoogeApp.filter('hostname', function() {
    return function(url) {
        return url.replace(/^https?:\/\//,'');
    };
});
