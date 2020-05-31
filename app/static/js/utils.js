function error(res) {
    alert("unable to get data from db, got:" + res.status + ";" + res.responseText + ". Please try again later");
}

function ajaxCall(url, tableId, onSuccess, onFailure, maxid) {
	var locations = buildSelectedLocations();
	if (locations.length == 0) {
	    return;
	}
	document.body.style.cursor = 'wait';
    document.getElementById("results").innerHTML = '';
	show_quary_reload();
	showTableByIter(tableId);
	var startDate = document.getElementById("start_date").value;
	var endDate = document.getElementById("end_date").value;
	var sliders_data = getSlidersDate();
	var word_list = getCheckedSearchWords();
	var max = 0;
	if (maxid != undefined) {
	    max = document.getElementById(maxid).value;
	}
	$.ajax({
		url: window.location.origin + url,
		data: {
			'user_name': document.getElementById("user").innerHTML,
			'locations_list': JSON.stringify(locations),
			'start_date': startDate,
			'end_date': endDate,
			'words_list': JSON.stringify(word_list),
			'sliders_data': JSON.stringify(sliders_data),
			'max_results': max
		},
		dataType: 'json',
		method: 'post',
		success: function (res, status) {
		    document.body.style.cursor = 'default';
			onSuccess(res, status);
		},
		error: function (res) {
		    document.body.style.cursor = 'default';
            error(res);
            onFailure(res);
		}
	});
}

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