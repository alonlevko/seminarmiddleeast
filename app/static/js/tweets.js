window.categoryDict = {};
window.conceptDict = {};
window.entitiesDict = {};
window.keywordsDict = {};
var $table = $('#ttable');

function hideTable(tableId) {
	document.getElementById(tableId).style.visibility = "hidden";
    document.getElementById(tableId).style.height = "0";
    document.getElementById(tableId).style.overflow = "hidden";
}

function showTable(tableId) {
    document.getElementById(tableId).style.visibility = "visible";
    document.getElementById(tableId).style.height = "1000";
    document.getElementById(tableId).style.overflow = "visible";

}

window.addEventListener('load', (event) => {
	document.getElementById("show_quary").onclick = loadQuarys;
	hideTable("users_table");
	hideTable("tweets_table");
	hideTable("origin_table");
	hideTable("most_retweeted_table");
	hideTable("first_time_table");
});

function parseTweetSendaway(t) {
	return {
	id:'<a target="_blank" href=http://www.twitter.com/' + t[2] + "/status/" + t[0] + ">" + t[0] + "</a>", //ID link to tweet
    text: t[1],
    username: '<a target="_blank" href=http://www.twitter.com/' + t[2] + ">" + t[2] + "</a>",
    userLocation: t[3],
    coordinates: t[4],
    placeName: t[5],
    created: t[6],
    //category: t[7],
    //concept: t[8],
    //entities: t[9],
    //entities_sentiment: t[10],
    //keywords: t[11],
    //keywords_sentiment: t[12]
	}
}

function updateTweetDictionarys(t) {
	if (t[7] in window.categoryDict) {
        window.categoryDict[t[7]]++;
    } else {
        window.categoryDict[t[7]] = 1;
    }
    if (t[8] in window.conceptDict) {
        window.conceptDict[t[8]]++;
    } else {
        window.conceptDict[t[8]] = 1;
    }
    if (t[9] in window.entitiesDict) {
        window.entitiesDict[t[9]]++;
    } else {
        window.entitiesDict[t[9]] = 1;
    }
	if (t[11] in window.keywordsDict) {
        window.keywordsDict[t[11]]++;
    } else {
        window.keywordsDict[t[11]] = 1;
    }
	
}

function buildChart(id, dictionary, name) {
    var ctx = document.getElementById(id);
    var items = Object.keys(dictionary).map(function(key) {
        return [key, dictionary[key]];
    });
    items.sort(function(first, second) {
        return second[1] - first[1];
    });
    var numbers = [];
    var names = []
    items.slice(0, 5).forEach(([key, value]) => {
        numbers.push(value);
        names.push(key);
    });
    new Chart(ctx, {
        type: 'doughnut',
         data: {
            datasets: [{
            data: numbers,
            backgroundColor: ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850"],
			label: id
            }],
            labels: names
            },
            options: {
                responsive: false,
                title: {
					display: true,
					text: name
				}
            }
        });
    }

function collectTweets() {
	var locations = buildSelectedLocations();
	if (locations.length == 0) {
	    return;
	}
	var word_list = getCheckedSearchWords();
	locations.forEach(function(elem) {
		$.ajax({
			url: window.location.origin + "/accumulate_tweets",
			data: {
				'user_name': document.getElementById("user").innerHTML,
				'locations_list': JSON.stringify([elem]),
				'words_list': JSON.stringify(word_list)
			},
			dataType: 'json',
			method: 'post',
			success: function (res, status) {},
			error: function (res) {
			    error(res);
   			}
			});
	});
}

function tweetNumToTime(tweetNum) {
    var timeToLoadTweetsSeconds = 0.01;
    var inSeconds = tweetNum * timeToLoadTweetsSeconds;
    var inMinutes = Math.floor(inSeconds / 60);
    inSeconds = Math.floor(inSeconds - (inMinutes * 60));
    return {'minutes': inMinutes, 'seconds': inSeconds};
}

function initTimer(prefix, button, whenToEnd) {
    var interval = setInterval(function() {
        if (whenToEnd['seconds'] == 0 && whenToEnd['minutes'] == 0) {
            button.innerHTML = "Inspect Tweets";
            clearInterval(interval);
            return;
        }
        if (whenToEnd['seconds'] == 0) {
            whenToEnd['minutes']--;
            whenToEnd['seconds'] = 59;
        } else {
            whenToEnd['seconds']--;
        }
        var text = prefix + ": " + whenToEnd['minutes'].toString() + "M:" + whenToEnd['seconds'].toString() + "S";
        button.innerHTML = text;
    }, 1000);
    return interval;
}
var tableIdList = ["tweets_table", "users_table", "origin_table", "most_retweeted_table", "first_time_table"];

function showTableByIter(tableid) {
    tableIdList.forEach(function(tablename) {
        if (tablename == tableid) {
            showTable(tablename);
        } else {
            hideTable(tablename);
        }
    });
}

function showTweets(button) {
    ajaxCall("/tweets-get", "tweets_table", function (res, status) {
				var data = [];
				$("#ttable").bootstrapTable('removeAll');
				res.forEach(function (t) {
					data.push(parseTweetSendaway(t));
					updateTweetDictionarys(t);
				});
				$("#ttable").bootstrapTable('append', data)
				button.disabled = false;
				button.innerHTML = "Inspect Tweets";
				//clearInterval(interval);
			}, function(res) {}, undefined, false, false);
}

function parseUserSendaway(t) {
	return {
        id: t[0], //ID link to tweet
        text: t[1],
        username: '<a target="_blank" href=http://www.twitter.com/' + t[2] + ">" + t[2] + "</a>",
        userLocation: t[3],
        coordinates: t[4],
        placeName: t[5],
        created: t[6],
		total_retweet_count: t[7],
		total_favorites_count: t[8],
		total_statuses_count: t[9],
		verified: t[10]
    }
}

function showUsers() {
    ajaxCall("/users-get", "users_table", function (res, status) {
		var data = [];
		res.forEach(function (t) {
			data.push(parseUserSendaway(t));
		});
		$('#utable').bootstrapTable('append', data)
    }, function(res) {}, undefined, false, false);
}

function buildAICharts() {
	var div = document.getElementById("AIcharts");
	div.innerHTML = `
		<canvas style="display: inline-block" id="categories_chart" width="400" height="400">categories</canvas>
        <canvas style="display: inline-block" id="concept_chart" width="400" height="400">concept</canvas>
        <canvas style="display: inline-block" id="entities_chart" width="400" height="400">entities</canvas>
        <canvas style="display: inline-block" id="keywords_chart" width="400" height="400">keywords</canvas>
		`;
	
	buildChart("categories_chart", window.categoryDict, "categories");
	buildChart("concept_chart", window.conceptDict, "concepts");
	buildChart("entities_chart",  window.entitiesDict, "entities");
	buildChart("keywords_chart", window.keywordsDict, "keywords");
}

function removeAICharts() {
	var div = document.getElementById("AIcharts");
	div.innerHTML = "";
}

function clearResults() {
    var div = document.getElementById("results");
    div.innerHTML = "";
    document.getElementById("tweets_table").style.visibility = "hidden";
}

function loadQuarys() {
    var locations = buildSelectedLocations();
    ajaxCall("/get_query_links", "origin_table", function (res, status) {
		   $('#otable').bootstrapTable('removeAll');
	       for (var i = 0; i < res.length; i++) {
	            $('#otable').bootstrapTable('append', {
                    region: locations[i].region,
                    place: locations[i].place,
                    link: `<a target="_blank" href="https://twitter.com/search?q=` + res + `&src=typed_query">Link</a><br>`
                });
	       }
	}, function (res) {}, undefined, false, false);
}

function show_quary_reload() {
    var button = document.getElementById("show_quary");
	button.innerHTML = "Twitter Origin";
	button.onclick = loadQuarys;
}

function removeQuarys() {
	var div = document.getElementById("results");
	div.innerHTML = "";
	hideTable("origin_table");
	$('#otable').bootstrapTable('removeAll');
    show_quary_reload();
}

function runAnalysis() {
    var command = document.getElementById("analytics").value;
    hideTable("tweets_table");
    hideTable("users_table");
	hideTable("origin_table");
    switch (command) {
            case "Popular_word_per_date":
                showTopWords()
                break;
            case "Word_trend":
                showTrends();
                break;
            case "Popularity_of_word_bank_per_place":
                showPopularityWords();
                break;
            case "Popular_word_per_place":
                showMostPopularWords();
                break;
            case "Opinion_Leaders":
                document.getElementById("results").innerHTML = '';
                document.getElementById('populars_dialog').show()
                break;
            case "First_Time":
                document.getElementById("results").innerHTML = '';
                document.getElementById('first_time_dialog').show()
                break;
            case "Most_Retweeted":
                document.getElementById("results").innerHTML = '';
                document.getElementById('most_retweeted_dialog').show()
                break;
            case "prompt":
            default:
                break;
    }
}
	