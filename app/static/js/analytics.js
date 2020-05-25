function calculateDayList(start, end) {
	for(var arr=[],dt=new Date(start); dt<=end; dt.setDate(dt.getDate()+1)){
		arr.push(new Date(dt));
	}
	return arr;
}

function getRandomColor() {
  var letters = '0123456789ABCDEF';
  var color = '#';
  for (var i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

function showTrends() {
	var div = document.getElementById("results");
	div.innerHTML = "";
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	var word_list = getCheckedSearchWords();
	var locations = buildSelectedLocations();
	if (locations.length == 0) {
	    return;
	}
	$.ajax({
		url: window.location.origin + "/word_trends_get",
		data: {
			'user_name': document.getElementById("user").innerHTML,
			'locations_list': JSON.stringify(locations),
			'words_list': JSON.stringify(word_list),
			'start_date': startDate,
			'end_date': endDate
		},
		dataType: 'json',
		method: 'post',
		success: function (res, status) {
			buildCanvas("trends_chart", div);
			buildTrendsChart(res, "trends_chart", startDate, endDate)
		},
		error: function (res) {
            error(res);
		}
	});
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
	var div = document.getElementById("results");
	div.innerHTML = "";
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	var locations = buildSelectedLocations();
	if (locations.length == 0) {
	    return;
	}
	div.innerHTML = "";
	$.ajax({
		url: window.location.origin + "/top_words_per_date_get",
		data: {
			'user_name': document.getElementById("user").innerHTML,
			'locations_list': JSON.stringify(locations),
			'start_date': startDate,
			'end_date': endDate
		},
		dataType: 'json',
		method: 'post',
		success: function (res, status) {
			buildCanvas("top_words_per_date_chart", div);
			buildTopWordsChart(res, "top_words_per_date_chart", startDate, endDate)
		},
		error: function (res) {
            error(res);
		}
	});
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
	var div = document.getElementById("results");
	div.innerHTML = "";
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	var locations = buildSelectedLocations();
	if (locations.length == 0) {
	    return;
	}
	var word_list = getCheckedSearchWords();
	div.innerHTML = "";
	$.ajax({
		url: window.location.origin + "/popularity_of_words_get",
		data: {
			'user_name': document.getElementById("user").innerHTML,
			'locations_list': JSON.stringify(locations),
			'words_list': JSON.stringify(word_list),
			'start_date': startDate,
			'end_date': endDate
		},
		dataType: 'json',
		method: 'post',
		success: function (res, status) {
			buildCanvas("popularity_of_words_chart", div);
			res = JSON.parse(res);
			var words = res['word_list'];
			buildPopularityChart(res, "popularity_of_words_chart", startDate, endDate, words, locations)
		},
		error: function (res) {
            error(res);
		}
	});
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
	var div = document.getElementById("results");
	div.innerHTML = "";
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	var locations = buildSelectedLocations();
	if (locations.length == 0) {
	    return;
	}
	$.ajax({
		url: window.location.origin + "/most_popular_word_get",
		data: {
			'user_name': document.getElementById("user").innerHTML,
			'locations_list': JSON.stringify(locations),
			'start_date': startDate,
			'end_date': endDate
		},
		dataType: 'json',
		method: 'post',
		success: function (res, status) {
            buildCanvas("most_popular_word_chart", div);
			buildPopularWordsChart(res, "most_popular_word_chart", startDate, endDate)
		},
		error: function (res) {
            error(res);
		}
	});
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
	var word_list = getCheckedSearchWords();
	var locations = buildSelectedLocations();
	if (locations.length == 0) {
	    return;
	}
	var max = document.getElementById("ftd_max").value;
	$.ajax({
		url: window.location.origin + "/first_time_get",
		data: {
			'user_name': document.getElementById("user").innerHTML,
			'locations_list': JSON.stringify(locations),
			'words_list': JSON.stringify(word_list),
			'start_date': startDate,
			'end_date': endDate,
			'max_results': max
		},
		dataType: 'json',
		method: 'post',
		success: function (res, status) {
			buildFirstTimeTables(res, "results", startDate, endDate)
		},
		error: function (res) {
            error(res);
		}
	});
}

function buildFirstTimeTables(res, id, start, end) {
	hideTable("tweets_table");
	hideTable("users_table");
	hideTable("origin_table");
	hideTable("most_retweeted_table");
	showTable("first_time_table");
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
	var word_list = getCheckedSearchWords();
	var locations = buildSelectedLocations();
	if (locations.length == 0) {
	    return;
	}
	var max = document.getElementById("mr_max").value;
	$.ajax({
		url: window.location.origin + "/most_retweeted_get",
		data: {
			'user_name': document.getElementById("user").innerHTML,
			'locations_list': JSON.stringify(locations),
			'words_list': JSON.stringify(word_list),
			'start_date': startDate,
			'end_date': endDate,
			'max_results': max
		},
		dataType: 'json',
		method: 'post',
		success: function (res, status) {
			buildMostRetweetedTable(res, "most_retweeted_chart", startDate, endDate)
		},
		error: function (res) {
            error(res);
		}
	});
}

function buildMostRetweetedTable(res, id, start, end) {
    hideTable("tweets_table");
	hideTable("users_table");
	hideTable("origin_table");
	hideTable("first_time_table");
	showTable("most_retweeted_table");
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
    hideTable("tweets_table");
	showTable("users_table");
	hideTable("origin_table");
	hideTable("first_time_table");
	hideTable("most_retweeted_table");
	var locations = buildSelectedLocations();
	if (locations.length == 0) {
	    return;
	}
	var word_list = getCheckedSearchWords();
	var sliders_data = getSlidersDate();
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	$("#utable").bootstrapTable('removeAll');
	$.ajax({
		url: window.location.origin + "/popular_users_get",
		data: {
			'user_name': document.getElementById("user").innerHTML,
			'locations_list': JSON.stringify(locations),
			'start_date': startDate,
			'end_date': endDate,
			'words_list': JSON.stringify(word_list),
			'sliders_data': JSON.stringify(sliders_data)
		},
		dataType: 'json',
		method: 'post',
		success: function (res, status) {
			var data = [];
			res.forEach(function (t) {
				data.push(parseUserSendaway(t));
			});
			$("#utable").bootstrapTable('append', data)
		},
		error: function (res) {
			alert("unable to get popular users from db, got:" + res.status + ". Please try again later");
		}
	});
}

function submitPopularUsers() {
    document.getElementById('populars_dialog').close()
    showPopularUsers();
}
