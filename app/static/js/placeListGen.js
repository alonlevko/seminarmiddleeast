var region_place_query_list = [];
var regions_places_dictionary = {};
var words = [];

window.addEventListener('load', (event) => {
  $.ajax({
    url: window.location.origin + "/get_regions_places",
    data: {
        'user_name': document.getElementById("user").innerHTML,
    },
    dataType: 'json',
	method: 'post',
    success: function (res, status) {
		var url = window.location.href + "/" + document.getElementById("user").innerHTML;
		regions_places_dictionary = res;
		var regionsSelectBox = document.getElementById("region_list_select");
		var placeSelectBox = document.getElementById("place_list_select");
		Object.keys(regions_places_dictionary).forEach(function(key) {
			$("#region_list_select").append('<option value="'+key+'">'+key+'</option>');
            // Refresh the selectpicker
            $("#region_list_select").selectpicker("refresh");
		});
		$(function () {
              $("#region_list_select").on("changed.bs.select", function(e, clickedIndex, newValue, oldValue) {
                var selectedD = $(this).find('option').eq(clickedIndex).text();
                if (newValue == true) {
                    regions_places_dictionary[selectedD].forEach(function(place_dict) {
                        $("#place_list_select").append('<option value="'+place_dict['name']+'">'+place_dict['name']+'</option>');
                        $("#place_list_select").selectpicker("refresh");
                    });
                } else {
                    regions_places_dictionary[selectedD].forEach(function(place_dict) {
                        var option = place_dict['name'];
                        var optionValue = "option[value='" + option + "']";
                        $("#place_list_select "+optionValue).remove();
                        $("#place_list_select").selectpicker("refresh");
                    });
                }
              });
        });
		//changeFunc();
    },
    error: function (res) {
        error(res);
    }
  });
  getAllWords("", "");
});


function AddFromSelect() {
	var regionsSelectBox = document.getElementById("region_list_select");
	var placeSelectBox = document.getElementById("place_list_select");
	var regionsSelectedValue = regionsSelectBox.options[regionsSelectBox.selectedIndex].value;
	var placeSelectedValue = placeSelectBox.options[placeSelectBox.selectedIndex].value;
	
	var element = {region: regionsSelectedValue, place: placeSelectedValue};
	if (region_place_query_list.some(e => (e.region === element.region) && (e.place === element.place))) {
		return;
	}	
	region_place_query_list.push(element);
	var div = document.getElementById("placeListGen");
	var button = document.createElement("button");
	button.innerHTML = regionsSelectedValue + ", " + placeSelectedValue+ ". ";
	var removeButton = 	function() {
		const index = region_place_query_list.indexOf(element);
		if (index > -1) {
			region_place_query_list.splice(index, 1);
		}
		this.remove();
	}
	button.addEventListener("click", removeButton);
	div.appendChild(button);

}

function buildLabelFromText(key, appendTo, addChangeFunc) {
    $("#" + appendTo).append('<option value="'+key+'">'+key+'</option>');
    $("#" + appendTo).selectpicker("refresh");
}
function changeFunc(key) {
    var changedClickBox = document.getElementById(key.id);
    if (changedClickBox.checked == true) {
        regions_places_dictionary[key.id].forEach(function(place_dict) {
            $("#place_list_select").append('<option value="'+place_dict['name'],+'">'+place_dict['name'],+'</option>');
        });
    } else {
        regions_places_dictionary[key.id].forEach(function(place_dict) {
            var optionValue = "option[value='" + place_dict['name'] + "']";
            $("#myselect "+optionValue).remove();
        });
    }
    $("#place_list_select").selectpicker("refresh");
}

function getDescendents(elem) {
    var descendents = elem.getElementsByTagName('*');
    descendents = Array.prototype.slice.call(descendents);
    return descendents;
}

function removeLabelFromText(key, removeFrom) {
    descendents = getDescendents(removeFrom);
    var element;
    for (var i = 0; i < descendents.length; ++i) {
        element = descendents[i];
        if (element.htmlFor == key || element.id == key) {
            element.remove();
        }
    }
}

var expanded = false;

function doesPlaceFitRegion(regionName, placeName) {
    var bool = false;
    regions_places_dictionary[regionName].forEach(function(place_dict) {
        if (place_dict['name'] == placeName) {
            bool = true;
        }
    });
    return bool;
}

function getSelectedPlaces(regionName) {
    var locations = [];
    $('#place_list_select :selected').each(function(i, value){
        var placeName = $(value).text();
        if (doesPlaceFitRegion(regionName, placeName)) {
            locations.push({region : regionName, place: placeName});
        }
    });
    return locations;
}

function buildSelectedLocations() {
    var locations_list = [];
    $('#region_list_select :selected').each(function(i, value){
        var region_name = $(value).text();
        locations_list = locations_list.concat(getSelectedPlaces(region_name));
    });
    return locations_list;
}

function openWordAdd() {
    document.getElementById("add_word_dialog").show();
    document.getElementById("plus_word").onclick = function () {
        document.getElementById("add_word_dialog").close();
        document.getElementById("plus_word").onclick = openWordAdd;
    };
}

function addWord() {
    var word = document.getElementById('word').value;
    getAllWords("", word);
    document.getElementById('word').value = "";
    document.getElementById("add_word_dialog").close();
}

function removeWord() {
    var word = document.getElementById('word').value;
    getAllWords(word, "");
    document.getElementById('word').value = "";
}

function removeSelectedWords() {
    var words = getCheckedSearchWords();
    getAllWords(words, "");
}

function getAllWords(toRemove, toAdd) {
  document.body.style.cursor = 'wait';
  setTimeout(function() {
      $.ajax({
        url: window.location.origin + "/get_search_words",
        data: {
            'user_name': document.getElementById("user").innerHTML,
            'to_add': JSON.stringify(toAdd),
            'to_remove': JSON.stringify(toRemove)
        },
        dataType: 'json',
        method: 'post',
        success: function (res, status) {
            document.body.style.cursor = 'default';
            words = res;
            updateWordsBox(words);
        },
        error: function (res) {
            document.body.style.cursor = 'default';
            error(res);
        }
      });
    }, 200);
}

function updateWordsBox(words) {
    $('#search_words_select').empty()
    for (var i = 0; i < words.length; i++) {
        $("#search_words_select").append('<option value="'+words[i]+'">'+words[i]+'</option>');
        $("#search_words_select").selectpicker("refresh");
    }
}

function getCheckedSearchWords() {
    var words = [];
    $('#search_words_select :selected').each(function(i, value){
        words[i] = $(value).text();
    });
    return words;
}