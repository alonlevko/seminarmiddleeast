function showTrends() {
    var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
    ajaxCall("/word_trends_get", "None", function (res, status) {
			buildCanvas("trends_chart", document.getElementById("results"));
			buildTrendsChart(res, "trends_chart", startDate, endDate)
		} , function(res) {});
}

function buildTrendsChart(res, id, start, end) {
	var daysList;
    var ctx = document.getElementById(id).getContext('2d');
    document.getElementById(id).style.backgroundColor = 'rgba(255,255,255, 0.3)';
	var dataSets = [];
	res.forEach(function (wordResult) {
		daysList = wordResult['dates'];
		dataSets.push({	data: wordResult['counter'],
						fill: false,
                        borderColor: getRandomColor(),
						label: wordResult['word']});
	});
	daysList.forEach(function (date, index, array) {
		var new_date = date.substring(0,4) + "-" + date.substring(4,6) + "-" + date.substring(6);
		array[index] = new_date;
	});
    new Chart(ctx, {
        type: 'line',
        data: {
			labels: daysList,
            datasets: dataSets,
            },
            options: {
                responsive: false,
                title: {
					display: true,
					text: "Word Trends"
				},
				scales: {
					yAxes: [{
						display: true,
						ticks: {
							beginAtZero: true,
							stepSize: 1,
							}
						}]
				},
            }
        });
}

function showTopWords() {
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	ajaxCall("/top_words_per_date_get", "None", function(res, status) {
		buildCanvas("top_words_per_date_chart", document.getElementById("results"));
		buildTopWordsChart(res, "top_words_per_date_chart", startDate, endDate);
	}, function (res) {} );
}

function buildTopWordsChart(res, id, start, end) {
    var ctx = document.getElementById(id).getContext('2d');
	var daysList = res['dates'];
	var color = getRandomColor();
    new Chart(ctx, {
        type: 'bar',
        data: {
			labels: daysList,
            datasets: [{
					data : res['counter'],
					backgroundColor: color,
					fill: false,
					label: "Popular Words"
			}]
            },
            options: {
                responsive: false,
                title: {
					display: true,
					text: "Word Trends"
				},
				scales: {
					yAxes: [{
						display: true,
						ticks: {
							beginAtZero: true,
							stepSize: 1,
							}
						}],
					xAxes: [{
						id:'xAxis1',
						display: true,
						type:"category",
						offset: true,
						ticks:{
							callback:function(label){
								var index = daysList.indexOf(label);
								if (index > -1) {
									return res['words'][index];
								}
								return "";
								}
							}
						}, {
						id:'xAxis2',
						display: true,
						type:"category",
						offset: true,
						gridLines: {
							drawOnChartArea: false,
						},
						ticks:{
							callback:function(label){
								return label;
							}
						}
					}],
				},
            }
        });
    }

function showPopularityWords() {
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	ajaxCall("/popularity_of_words_get", "None", function (res, status) {
	    buildCanvas("popularity_of_words_chart", document.getElementById("results"));
		res = JSON.parse(res);
		var words = res['word_list'];
		buildPopularityChart(res, "popularity_of_words_chart", startDate, endDate, words, locations);
	}, function (res) {})
}

function buildPopularityChart(res, id, start, end, word_list, locations) {
    var ctx = document.getElementById(id).getContext('2d');
    var dataSets = [];
    locations.forEach(function (loc) {
        dataSets.push({	data: new Array(word_list.length),
						borderColor: getRandomColor(),
						backgroundColor: getRandomColor(),
						label: loc['place']});
    });
    for (var i = 0; i < res.rows; i++) {
        var set = dataSets.find(element => element.label == res['place_name'][i]);
        var index = word_list.findIndex(element => element == res['word'][i])
        set.data[index] = res['counter'][i]
    }
    new Chart(ctx, {
        type: 'bar',
        data: {
			labels: word_list,
            datasets: dataSets,
            },
            options: {
                responsive: false,
                title: {
					display: true,
					text: "Popularity Of Words"
				},
				scales: {
					yAxes: [{
						display: true,
						ticks: {
							beginAtZero: true,
							stepSize: 1,
							}
						}]
				},
            }
        });
    }

function buildCanvas(id, div) {
    var canvas = document.createElement("canvas");
    canvas.id = id;
	canvas.width = window.innerWidth * 0.8;
    canvas.height = window.innerHeight * 0.8;
    canvas.style.display = "inline-block";
    div.appendChild(canvas);
}

function showMostPopularWords() {
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	ajaxCall("/most_popular_word_get", "None", function (res, status) {
        buildCanvas("most_popular_word_chart", document.getElementById("results"));
		buildPopularWordsChart(res, "most_popular_word_chart", startDate, endDate)
	}, function (res) {});
}

function buildPopularWordsChart(res, id, start, end) {
    var ctx = document.getElementById(id);
    new Chart(ctx, {
        type: 'bar',
        data: {
			labels: res['places'],
            datasets: [{
				data: res['counters'],
				backgroundColor: getRandomColor(),
				label: "Count"
            }],
            },
            options: {
                responsive: false,
                title: {
					display: true,
					text: "Most Popular Word"
				},
				scales: {
					yAxes: [{
						display: true,
						ticks: {
							beginAtZero: true,
							stepSize: 1,
							}
						}],
					xAxes: [{
						id:'words',
						display: true,
						type:"category",
						offset: true,
						ticks:{
							callback:function(label){
								var index = res['places'].indexOf(label);
								if (index > -1) {
									return res['words'][index];
								}
								return "";
								}
							}
						}, {
						id:'places',
						display: true,
						type:"category",
						offset: true,
						gridLines: {
							drawOnChartArea: false,
						},
						ticks:{
							callback:function(label){
								return label;
							}
						}
					}],
				},
            }
        });
    }

function showFirstTime() {
    document.getElementById('first_time_dialog').close()
    var div = document.getElementById("results");
	div.innerHTML = "";
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	ajaxCall("/first_time_get", "first_time_table", function(res, status) {
	buildFirstTimeTables(res, "results", startDate, endDate);
	}, function (res) {}, "ftd_max");
}

function buildFirstTimeTables(res, id, start, end) {
    var tableData = [];
    for (var i = 0; i < res.length; i++ ){
        for (var j = 0; j < res[i]["row_data"].length; j++) {
            tableData.push({
                id: '<a target="_blank" href=http://www.twitter.com/' + res[i]["row_data"][j][2] + "/status/" + res[i]["row_data"][j][0] + ">" + res[i]["row_data"][j][0] + "</a>",
                text: res[i]["row_data"][j][1],
                screen_name: '<a target="_blank" href=http://www.twitter.com/' + res[i]["row_data"][j][2] + ">" + res[i]["row_data"][j][2] + "</a>",
                full_date: res[i]["row_data"][j][3],
                time_rnk: res[i]["row_data"][j][4],
                search_word: res[i]["word"]
            })
        }
    }
    $("#ftttable").bootstrapTable('removeAll');
    $("#ftttable").bootstrapTable('append', tableData);
}

function showMostRetweeted(){
    document.getElementById('most_retweeted_dialog').close()
    var div = document.getElementById("results");
	div.innerHTML = "";
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	ajaxCall("/most_retweeted_get", "most_retweeted_table", function (res, status) {
			buildMostRetweetedTable(res, "most_retweeted_chart", startDate, endDate)
	}, function (res) {}, "mr_max");
}

function buildMostRetweetedTable(res, id, start, end) {
    var tableData = [];
    for (var i = 0; i < res.length; i++ ){
            tableData.push({
                id: '<a target="_blank" href=http://www.twitter.com/' + res[i][2] + "/status/" + res[i][0] + ">" + res[i][0] + "</a>",
                text: res[i][1],
                screen_name: '<a target="_blank" href=http://www.twitter.com/' + res[i][2] + ">" + res[i][2] + "</a>",
                full_date: res[i][3],
                retweet_count: res[i][4],
                retweet_rnk: res[i][5],
                search_word: res[i][6]
            })
        }
    $("#mrtable").bootstrapTable('removeAll');
    $("#mrtable").bootstrapTable('append', tableData);
}

var sliderNames = ["followers_slider", "retweet_slider", "favorites_slider", "tweets_slider"];

window.addEventListener('load', (event) => {
	sliderNames.forEach(id => createSlider(id));
})

function createSlider(id) {
	var slider = document.getElementById(id);
	noUiSlider.create(slider, {
		start: [40, 60],
		connect: true,
		range: {
			'min': 0,
			'max': 100
		},
		step: 1,
		behaviour: 'tap-drag',
		tooltips: true,
		pips: {
        mode: 'steps',
        stepped: true,
        density: 1
		}
	});
}

function getSlidersDate() {
    var array = [];
    for (var i = 0; i < sliderNames.length; i++) {
        var data = document.getElementById(sliderNames[i]).noUiSlider.get();
        array.push(data);
    }
    return array;
}

function showPopularUsers() {
	ajaxCall("/popular_users_get", "users_table", function (res, status) {
	        $("#utable").bootstrapTable('removeAll');
			var data = [];
			res.forEach(function (t) {
				data.push(parseUserSendaway(t));
			});
			$("#utable").bootstrapTable('append', data)
		}, function (res) {} );
}

function submitPopularUsers() {
    document.getElementById('populars_dialog').close()
    showPopularUsers();
}
