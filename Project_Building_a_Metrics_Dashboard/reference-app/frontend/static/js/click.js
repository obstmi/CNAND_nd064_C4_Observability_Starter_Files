$(document).ready(function () {

    $("#firstbutton").click(function () {
        $.ajax({
            url: "http://localhost:8081/", success: function (result) {
                $("#firstbutton").toggleClass("btn-primary:focus");
                }
        });
    });
    $("#secondbutton").click(function () {
        $.ajax({
            url: "http://localhost:8081/schnuppi", success: function (result) {
                $("#secondbutton").toggleClass("btn-primary:focus");
            }
        });
    });    
});