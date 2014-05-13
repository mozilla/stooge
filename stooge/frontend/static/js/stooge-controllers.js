// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/

var stoogeControllers = angular.module('stoogeControllers', []);

stoogeControllers.config(['$routeProvider', function($routeProvider) {
    $routeProvider
        .when('/results/:scanId', {
            templateUrl: 'static/partials/scan-results.html',
            controller: 'ScanResultsController'
        })
        .otherwise({
            redirectTo: '/results/latest'
        });
}]);

stoogeControllers.controller('ScanResultsController', ['$scope', '$http', 'Scan',
    function ($scope, $http, Scan) {
        $scope.scan = undefined;
        $scope.sites = undefined;

        Scan.query({id:"last"}, function (response) {
            var scan = response.data;
            scan.sites = _.sortBy(scan.sites, sortScanSites);
            $scope.scan = scan;
            $scope.sites = scan.sites;

            var owner = "all";
            if ($scope.session.email.match(/@mozilla.com/)) {
                owner = "moco";
            } else if ($scope.session.email.match(/@mozillafoundation.org/)) {
                owner = "mofo";
            } else {
                owner = "community";
            }
            $scope.filterOnOwner(owner);
        });

        $scope.filterOwner = "all";
        $scope.filterType = "all";

        $scope.filterOnOwner = function(owner) {
            $scope.filterOwner = owner;
            if ($scope.filterOwner === "all" && $scope.filterType === "all") {
                $scope.sites = $scope.scan.sites;
            } else if ($scope.filterOwner === "all") {
                $scope.sites = _.filter($scope.scan.sites, function (site) { return site.type === $scope.filterType; });
            } else if ($scope.filterType === "all") {
                $scope.sites = _.filter($scope.scan.sites, function (site) { return site.owner === $scope.filterOwner; });
            } else {
                $scope.sites = _.filter($scope.scan.sites, function (site) { return site.owner === $scope.filterOwner && site.type === $scope.filterType; });
            }
        };

        $scope.filterOnType = function(type) {
            $scope.filterType = type;
            if ($scope.filterOwner === "all" && $scope.filterType === "all") {
                $scope.sites = $scope.scan.sites;
            } else if ($scope.filterOwner === "all") {
                $scope.sites = _.filter($scope.scan.sites, function (site) { return site.type === $scope.filterType; });
            } else if ($scope.filterType === "all") {
                $scope.sites = _.filter($scope.scan.sites, function (site) { return site.owner === $scope.filterOwner; });
            } else {
                $scope.sites = _.filter($scope.scan.sites, function (site) { return site.owner === $scope.filterOwner && site.type === $scope.filterType; });
            }
        };

        $scope.bugzillaLink = function (site) {
            var hostname = site.url.replace(/^https?:\/\//,'');
            return "https://bugzilla.mozilla.org/buglist.cgi?v4=[site%3A" + hostname + "]&f1=bug_group&o3=equals&v3=" + hostname + "&j2=OR&o1=equals&f4=status_whiteboard&query_format=advanced&f3=component&o4=substring&f2=OP&bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&f5=CP&v1=websites-security";
        };

        $scope.sslLabsLink = function (site) {
            var hostname = site.url.replace(/^https?:\/\//,'');
            return "https://www.ssllabs.com/ssltest/analyze.html?d=" + hostname;
        }
    }]);
