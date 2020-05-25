var $table = $('#ttable');

function parseUserSendaway(t) {
	return {
        id:'<a target="_blank" href=http://www.twitter.com/' + t[2] + "/status/" + t[0] + ">" + t[0] + "</a>", //ID link to tweet
        text: t[1],
        username: '<a target="_blank" href=http://www.twitter.com/' + t[2] + ">" + t[2] + "</a>",
        userLocation: t[3],
        coordinates: t[4],
        placeName: t[5],
        created: t[6],
		total_retweet_count: t[7],
		total_favorites_count: t[8],
		total_replies_count: t[9],
		total_quoted_count: t[10],
		verified: t[11]
    }
}

function showUsers() {
	$table.bootstrapTable('removeAll');
	region_place_query_list.forEach(function(elem) {
		$.ajax({
			url: window.location.origin + "/users-get",
			data: {
				'user_name': document.getElementById("user").innerHTML,
				'region_name': elem.region,
				'place_name': elem.place,
			},
			dataType: 'json',
			method: 'post',
			success: function (res, status) {
				var data = [];
				res.forEach(function (t) {
					data.push(parseUserSendaway(t));
				});
				$table.bootstrapTable('append', data)
			},
			error: function (res) {
                error(res);
			}
		});
	});
}
	

	