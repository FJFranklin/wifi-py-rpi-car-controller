/* Asynchronous request from server, sending and receiving text
 * 
 * (Take a look at https://www.html5rocks.com/en/tutorials/file/xhr2/ for getting binary data, e.g., images)
 */
function send_request_query (str_name_namespace, str_value_query, callback_function) {
    var query = new XMLHttpRequest ();

    query.open ("GET", "/query?name=" + str_name_namespace + "&value=" + str_value_query);
    query.responseType = "text";
    query.onload = function (e) {
        callback_function (this.response);
    }
    query.send (); // TODO? Implement error checking?
}

/* Here the text response from the server is two comma-seperated variables
 */
var last_h = "";
var last_m = "";
var last_s = "";

function clock_update (text) {
    var coords = text.split (','); // comma-separated list of numbers -> array of strings

    if (coords.length == 3) {
	if (last_h != coords[0]) {
	    last_h = coords[0];
            var h_hand = document.getElementById ("hours");
	    var rotate = "rotate(" + last_h + ")";
            h_hand.setAttribute ("transform", rotate);
	}
	if (last_m != coords[1]) {
	    last_m = coords[1];
            var m_hand = document.getElementById ("minutes");
	    var rotate = "rotate(" + last_m + ")";
            m_hand.setAttribute ("transform", rotate);
	}
	if (last_s != coords[2]) {
	    last_s = coords[2];
            var s_hand = document.getElementById ("seconds");
	    var rotate = "rotate(" + last_s + ")";
            s_hand.setAttribute ("transform", rotate);
	}
    }
}
function periodic_update () {
    /* In this Circles example, only the blue circle's position needs to be updated periodically
     */
    send_request_query ("clock", "time", clock_update);
}
function get_started () {
    window.setInterval (periodic_update, 100); // interval in milliseconds
}
window.onload = get_started;
