// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/

var stoogeServices = angular.module('stoogeServices', ['ngResource']);

stoogeServices.factory('Scan', ['$resource',
    function($resource){
        return $resource("/api/scan/:id", {}, {
            query: { method: "GET", isArray: false }
        });
    }]);

stoogeServices.factory('Bugs', ['$resource', '$http',
    function($resource, $http){
        return $resource("/api/scan/:scanId/site/:siteId/bugs", {}, {
            get: {
                method: "GET",
                isArray: true,
                format: 'json',
                transformResponse: function (response, headers) {
                    response = angular.fromJson(response);
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
                    return response.data;
                }
            }
        });
    }]);
