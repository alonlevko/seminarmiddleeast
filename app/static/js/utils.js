function error(res) {
    alert("unable to get data from db, got:" + res.status + ";" + res.responseText + ". Please try again later");
}