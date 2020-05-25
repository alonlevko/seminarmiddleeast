function showMostPopularWords() {
	var div = document.getElementById("most_popular_word_div");
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	div.innerHTML = "";
	$.ajax({
		url: window.location.origin + "/most_popular_word_get",
		data: {
			'user_name': document.getElementById("user").innerHTML,
			'locations_list': JSON.stringify(region_place_query_list),
			'start_date': startDate,
			'end_date': endDate 
		},
		dataType: 'json',
		method: 'post',
		success: function (res, status) {
			div.innerHTML = `<canvas style="display: inline-block" id="most_popular_word_chart" width="400" height="400">Word Trends Per Date</canvas>`;
			buildPopularWordsChart(res, "most_popular_word_chart", startDate, endDate)
		},
		error: function (res) {
            error(res);
		}
	});
}


function buildPopularWordsChart(res, id, start, end) {
	var daysList = function(start, end) {
		for(var arr=[],dt=new Date(start); dt<=end; dt.setDate(dt.getDate()+1)){
			arr.push(new Date(dt));
		}
		return arr;
	};
    var ctx = document.getElementById(id);
    new Chart(ctx, {
        type: 'bar',
        data: {
			labels: word_list,
            datasets: [{
				data: res,
				backgroundColor: ["#3e95cd"],
				label: "Count"
            }],
            labels: names
            },
            options: {
                responsive: false,
                title: {
					display: true,
					text: "Most Popular Word"
				}
            }
        });
    }