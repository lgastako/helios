$(function() {
  var chartGenerated = false;
  $("#chart").click(function(e) {
    e.preventDefault();
    $("#chart-area").toggle();
    if (!chartGenerated) {
      chartGenerated = true;
      var url = "/count/" + collection_name + "/chart";
      if (groupBy) {
          url += "?group_by=" + groupBy;
      }
      $("#chart-area iframe").attr("src", url);
    }
    return false;
  });
});