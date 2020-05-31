function openCity(evt, cityName) {
  // Declare all variables
  var i, tabcontent, tablinks;

  // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Get all elements with class="tablinks" and remove the class "active"
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  // Show the current tab, and add an "active" class to the button that opened the tab
  document.getElementById(cityName).style.display = "block";
  evt.currentTarget.className += " active";
}

function removeRegion(regionName) {
    document.getElementById("id_from_region").value = regionName;
    document.getElementById("removeForm").submit();
}

function removePlace(regionName, placeName) {
    document.getElementById("id_from_region").value = regionName;
    document.getElementById("id_from_place").value = placeName;
    document.getElementById("removeForm").submit();
}

function hideElement(id) {
    document.getElementById(id).style.visibility = "hidden";
    document.getElementById(id).style.height = "0";
    document.getElementById(id).style.overflow = "hidden";
}

function showElement(id, height) {
    document.getElementById(id).style.visibility = "visible";
    document.getElementById(id).style.height = height;
    document.getElementById(id).style.overflow = "visible";
}

function addRegionTab() {
    var height = $(".tablinks").height();
    //height = height - 2;
    var sheight = String(height) + "px";
    showElement("region", sheight);
    showElement("arrow", sheight);
    height = height / 2;
    height = String(height) + "px";
    document.getElementById("region").style.marginTop = height;
    //document.getElementById("ar"row").style.marginTop = height;
    //document.getElementById("arr").style.height = sheight;
    //document.getElementById("arr").style.marginTop = height;
    document.getElementById("addRegion").onclick = submitRegionName;
}

function submitRegionName() {
    document.getElementById("addRegion").onclick = addRegionTab;
    hideElement("region");
    hideElement("arrow");
    // put name from textbox into region form
    var val = document.getElementById("region").value;
    document.getElementById("id_region_name").value = val;
    document.getElementById("region_form").submit();
}

function addPlaceRow(key) {
    //showElement("addPlaceRow_" + key);
    var text = $('.tablinks.active').text();
    document.getElementById("addPlace").onclick = function () {
        hideElement("place_form");
        document.getElementById("addPlace").onclick = addPlaceRow;
        document.getElementById("addPlace").innerHTML = "&#43;";
    };
    document.getElementById("addPlace").innerHTML = "&#8722;";
    showElement("place_form");
    document.getElementById("id_upper_region_name").value = text;
}

var slim_id_list = ["id_place_name", "id_latitude", "id_longitude", "id_radius", "id_language", "id_upper_region_name"];
function submitPlaceStuff(regionName) {
    slim_id_list.forEach(function (elemID) {
        if(elemID == "id_upper_region_name") {
            var name = regionName;
            document.getElementById(elemID).value = name;
            return;
        }
        var firstId = elemID + "_" + regionName;
        var fromFirst = document.getElementById(firstId).value;
        var type = typeof fromFirst;
        document.getElementById(elemID).value = fromFirst;
    });
    document.getElementById("place_form").submit();
}