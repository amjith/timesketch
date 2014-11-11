/*
Copyright 2014 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

'use strict';

var directives = angular.module('timesketch.directives', []);

directives.directive('d3Heatmap', ['d3Service', function(d3Service) {
    return {
        restrict: 'EA',
        scope: {},
        link: function(scope, element, attrs) {
            d3Service.d3().then(function(d3) {
                // our d3 code will go here

                    var margin = { top: 50, right: 0, bottom: 100, left: 30 };
                    var svgWidth = 1635 - margin.top - margin.bottom;
                    var svgHeight = 500 - margin.top - margin.bottom;
                    var rectSize = Math.floor(svgWidth / 24);
                    var days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
                    var hours = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23"];

                    var svg = d3.select("#chart").append("svg")
                        .attr("width", svgWidth + margin.left + margin.right)
                        .attr("height", svgHeight + margin.top + margin.bottom)
                        .append("g")
                        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


                scope.$parent.$watch('meta', function (newval, oldval) {

                    if(scope.$parent.meta) {
                        var data = scope.$parent.meta.aggregations.per_hour;
                    } else {
                        var data = false
                    }
                    return scope.render(data)
                }, true);

                scope.render = function(data) {

                    svg.selectAll('*').remove();


                    var max_value_initial = d3.max(data, function (d) {
                        return d.doc_count;
                    });
                    var max_value = max_value_initial;

                    if (max_value_initial > 100000) {
                        max_value = max_value_initial / 10;
                    } else if (max_value_initial == 0) {
                        max_value = 1
                    }

                    var colors = [];
                    var genColor = d3.scale.linear()
                        .domain([0, max_value / 2, max_value])
                        .range(["white", "#3498db", "red"]);

                    for (var i = 0; i < max_value; i++) {
                        colors.push(genColor(i));
                    }
                    var num_buckets = colors.length;

                    var colorScale = d3.scale.quantile()
                        .domain([0, num_buckets - 1, max_value_initial])
                        .range(colors);

                    var dayLabels = svg.selectAll(".dayLabel")
                        .data(days)
                        .enter().append("text")
                        .text(function (d) {
                            return d;
                        })
                        .attr("x", 0)
                        .attr("y", function (d, i) {
                            return i * rectSize;
                        })
                        .style("text-anchor", "end")
                        .attr("transform", "translate(-6," + rectSize / 1.5 + ")");

                    var hourLabels = svg.selectAll(".hourLabel")
                        .data(hours)
                        .enter().append("text")
                        .text(function (d) {
                            return d;
                        })
                        .attr("x", function (d, i) {
                            return i * rectSize;
                        })
                        .attr("y", 0)
                        .style("text-anchor", "middle")
                        .attr("transform", "translate(" + rectSize / 2 + ", -6)");

                    var heatMap = svg.selectAll(".hour")
                        .data(data)
                        .enter().append("rect")
                        .attr("x", function (d) {
                            return (d.hour) * rectSize;
                        })
                        .attr("y", function (d) {
                            return (d.day - 1) * rectSize;
                        })
                        .attr("class", "bordered")
                        .attr("width", rectSize)
                        .attr("height", rectSize)
                        .style("fill", colors[0]);


                    heatMap.transition().duration(700)
                        .style("fill", function (d) {
                            return colorScale(d.doc_count);
                        });

                    heatMap.append("title").text(function (d) {
                        return d.doc_count;
                    });
                }
            });
        }};
}]);

directives.directive("butterbar", function() {
    return {
        restrict : "A",
        link : function(scope, element, attrs) {
            scope.$on("httpreq-start", function(e) {
                element.css({"display": "block"});
            });

            scope.$on("httpreq-complete", function(e) {
                element.css({"display": "none"});
            });
        }
    };
});

directives.directive('timelineColor', function () {
    return {
      restrict: 'A',
      link: function (scope, elem, attrs) {
          var tlcolors = scope.meta.timeline_colors
          elem.css("background", "#" + tlcolors[scope.$parent.event.es_index])
      }
    }
});

directives.directive('timelineName', function () {
    return {
      restrict: 'A',
      link: function (scope, elem, attrs) {
          var tlnames = scope.meta.timeline_names
          elem.addClass("label")
          elem.css("color", "#999")
          elem.append(tlnames[scope.$parent.event.es_index])
      }
    }
});

directives.directive('indexChooser', function() {
    return {
      restrict: 'A',
      scope: {
        filter: '=',
        search: '=',
        meta: '='
      },
      link: function (scope, elem, attrs) {
        scope.$watch("filter", function(value) {
            var i = scope.filter.indexes.indexOf(attrs.index);
            if (i == -1) {
                elem.css('color', '#d1d1d1');
                elem.find(".color-box").css('background', '#e9e9e9');
                elem.find(".t").css('text-decoration', 'line-through');
                elem.find("input").prop("checked", false);
            } else {
                elem.css('color', '#333');
                elem.find(".t").css('text-decoration', 'none');
                elem.find("input").prop("checked", true);
            }
        })
        elem.bind('click', function() {
            var i = scope.filter.indexes.indexOf(attrs.index);
            if (i > -1) {
                scope.filter.indexes.splice(i, 1);
                elem.css('color', '#d1d1d1');
                elem.find(".color-box").css('background', '#e9e9e9');
                elem.find(".t").css('text-decoration', 'line-through');
                elem.find("input").prop("checked", false);
            } else {
                scope.filter.indexes.push(attrs.index)
                elem.css('color', '#333');
                elem.find(".t").css('text-decoration', 'normal');
                elem.find('.color-box').css('background', "#" + scope.meta.timeline_colors[attrs.index])
                elem.find("input").prop("checked", true);

            }
            scope.search()
        })
      }
    }
});

directives.directive('indexDisabler', function() {
    return {
      restrict: 'A',
      scope: {
        filter: '=',
        search: '=',
        meta: '='
      },
      link: function (scope, elem, attrs) {
        elem.bind('click', function() {
            var b = document.getElementsByClassName("timelinebox")
            for (var i=0; i < b.length; i++) {
                var e = $(b[i])
                e.css('color', '#d1d1d1');
                e.find(".color-box").css('background', '#e9e9e9');
                e.find(".t").css('text-decoration', 'line-through');
                e.find("input").prop("checked", false);
            }

            scope.filter.indexes = []
            scope.search()
        })
      }
    }
});

directives.directive('indexEnabler', function() {
    return {
      restrict: 'A',
      scope: {
        filter: '=',
        search: '=',
        meta: '='
      },
      link: function (scope, elem, attrs) {

        elem.bind('click', function() {
            var name_to_index = {}
            for (var index in scope.meta.timeline_names) {
                var _name = scope.meta.timeline_names[index]
                name_to_index[_name] = index
            }
            var b = document.getElementsByClassName("timelinebox")
            for (var i=0; i < b.length; i++) {
                var e = $(b[i]);
                var name = String(e[0].innerText).trim();
                e.css('color', '#333');
                e.find(".t").css('text-decoration', 'normal');
                e.find('.color-box').css('background', "#" + scope.meta.timeline_colors[name_to_index[name]])
                e.find("input").prop("checked", true);
            }
            scope.filter.indexes = []
            for (var n in scope.meta.timeline_names) {
                scope.filter.indexes.push(n)
            }
            scope.search()

        })
      }
    }
});
