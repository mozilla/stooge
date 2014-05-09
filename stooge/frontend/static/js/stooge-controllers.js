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
        .when('/results/:scanId/site/:siteId', {
            templateUrl: 'static/partials/scan-details.html',
            controller: 'ScanDetailsController'
        })
        .when('/websecbugs', {
            templateUrl: 'static/partials/websecbugs.html',
            controller: 'WebSecBugsController'
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
    }]);

stoogeControllers.controller('ScanDetailsController', ['$scope', 'Bugs', '$routeParams',
    function ($scope, Bugs, $routeParams) {
        Bugs.get({scanId:$routeParams.scanId, siteId:$routeParams.siteId}, function (response) {
            $scope.bugs = response;
            console.dir($scope.bugs);
        });
    }]);

stoogeControllers.controller('WebSecBugsController', ['$scope', '$http',
    function ($scope, $http) {
        $scope.loading = true;

        $scope.filterName = "all";
        $scope.sortName = "count";

        var countTotalBugs = function()
        {
            return _.chain($scope.sites)
                .map(function (site) {return site.new + site.unconfirmed;})
                .reduce(function (memo, num) {return memo + num;}, 0)
                .value();
        };

        $scope.filter = function(what)
        {
            $scope.filterName = what;

            switch (what) {
            case "all": {
                $scope.sites = $scope.allSites;
                break;
            }
            case "moco": {
                $scope.sites = _.filter($scope.allSites, function(site) {return MOCO_SITES.indexOf(site.name) != -1;});
                break;
            }
            case "mofo": {
                $scope.sites = _.filter($scope.allSites, function(site) {return MOFO_SITES.indexOf(site.name) != -1;});
                break;
            }
            case "thirdparty": {
                $scope.sites = _.filter($scope.allSites, function(site) {return THIRD_PARTY_SITES.indexOf(site.name) != -1;});
            }
            }

            $scope.sitesBugCount = countTotalBugs();
            $scope.sort($scope.sortName);
        };

        $scope.sort = function(what)
        {
            $scope.sortName = what;

            switch (what) {
            case "count": {
                $scope.sites = _.sortBy($scope.sites, function(site) { return site.unconfirmed + site.new; }).reverse();
                break;
            }
            case "age": {
                $scope.sites = _.sortBy($scope.sites, function(site) { return site.averageAge; }).reverse();
                break;
            }
            case "name": {
                $scope.sites = _.sortBy($scope.sites, function(site) { return site.name; });
                break;
            }
            }
        };

        $http.get("/api/websecbugs")
            .success(function (response, status) {
                $scope.bugs = response.data;
                $scope.loading = false;

                _.each(response.data, function(bug) {
                    if (bug.creation_time) {
                        bug.creation_time = moment(bug.creation_time);
                    }
                    if (bug.last_change_time) {
                        bug.last_change_time = moment(bug.last_change_time);
                    }
                    if (bug.history) {
                        _.each(bug.history, function (event) {
                            event.change_time = moment(event.change_time);
                        });
                    }
                    if (!bug.depends_on) {
                        bug.depends_on = [];
                    }
                    bug.age = moment().diff(bug.creation_time, 'days');
                    bug.ageLabel = "default";
                    if (bug.age < 14) {
                        bug.ageLabel = "success";
                    } else if (bug.age < 28) {
                        bug.ageLabel = "warning";
                    } else {
                        bug.ageLabel = "important";
                    }
                        bug.isAssigned = (bug.assigned_to !== "nobody@mozilla.org" && bug.assigned_to !== "nobody");
                });

                var parseSites = function parseSites(s) {
                    var sites = [];
                    _.each(s.match(/(\[site:(.+?)\])/gi), function (match) {
                        sites.push(/\[site:(.+?)\]/.exec(match)[1]);
                    });
                    return sites;
                };

                var sites = {};
                _.each($scope.bugs, function(bug) {
                    if (bug.status === 'UNCONFIRMED' || bug.status === 'NEW' || bug.status === "REOPENED" || bug.status == "ASSIGNED") {
                        //bugzillaService.cleanupBug(bug);
                        //bug.shortStatus = shortStatus(bug).status;
                        //bug.shortStatusColor = shortStatus(bug).color;
                        _.each(parseSites(bug['whiteboard']), function (site) {
                            if (!sites[site]) {
                                sites[site] = {name:site,unconfirmed:0,resolved:0,new:0,verified:0,averageAge:0,bugs:[]};
                            }
                            sites[site].bugs.push(bug);
                            sites[site][bug.status.toLowerCase()]++;
                            sites[site].averageAge += bug.age;
                        });
                    }
                });

                _.each(sites, function(site) {
                    site.averageAge = Math.floor(site.averageAge / (site.new + site.unconfirmed));
                    site.averageAgeLabel = "default";
                    if (site.averageAge < 7) {
                        site.averageAgeLabel = "success";
                    } else if (site.averageAge< 24) {
                        site.averageAgeLabel = "warning";
                    } else {
                        site.averageAgeLabel = "important";
                    }
                    //site.bugzillaAllOpenBugsLink = "https://bugzilla.mozilla.org/buglist.cgi?type0-1-0=substring;field0-1-0=status_whiteboard;field0-0-0=bug_group;query_format=advanced;value0-1-0=[site%3A" + site.name + "];bug_status=UNCONFIRMED;bug_status=NEW;type0-0-0=equals;value0-0-0=websites-security";
                });

                $scope.allSites = _.chain(sites)
                    .values()
                    .filter(function (site) { return site.new > 0 || site.unconfirmed > 0 })
                    .value();

                $scope.filter('all');
            })
            .error(function (response, status) {
                // TODO
            });
    }]);
