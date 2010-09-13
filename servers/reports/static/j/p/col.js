$(function() {
  var chartGenerated = false;
  $("#chart").click(function(e) {
    e.preventDefault();
    $("#chart-area").toggle();
    window.scrollTo(0, $("#chart-area").offset().top);
    if (!chartGenerated) {
      chartGenerated = true;
      var url = "/col/" + collection_name + "/chart";
      $("#chart-area iframe").attr("src", url);
    }
    return false;
  });
  $("#clear").click(function() {
   $("form input[name=query]").attr("value", "");
   $("form").submit();
   return false;
  });
});