/* Red circle moves in response to button-down events; X & Y values update according to mouse position events
 */
function red_circle (event, type) {
    var svg_box = document.getElementById ("foreground");
    var value_x = document.getElementById ("value_x");
    var value_y = document.getElementById ("value_y");

    var rect = svg_box.getBoundingClientRect ();

    var x = event.clientX - rect.x;
    var y = event.clientY - rect.y;

    if (x < 0) {
	x = 0;
    }
    if (y < 0) {
	y = 0;
    }
    if (x > rect.width) {
	x = rect.width;
    }
    if (y > rect.height) {
	y = rect.height;
    }

    value_x.innerHTML = (2 * x / rect.width  - 1).toFixed (3);
    value_y.innerHTML = (2 * y / rect.height - 1).toFixed (3);

    if ((event.buttons === 0) && (event.button === 0)) {
	x = rect.width / 2;
	y = rect.height / 2;
    }

    var c_red = document.getElementById ("circle_red");

    c_red.setAttribute ("cx", x.toFixed (3));
    c_red.setAttribute ("cy", y.toFixed (3));
}

function e_down (event) {
    red_circle (event, "down");
}
function e_up (event) {
    red_circle (event, "up");
}
function e_over (event) {
    red_circle (event, "over");
}
function e_move (event) {
    red_circle (event, "move");
}
function e_out (event) {
    red_circle (event, "out");
}
	
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
function blue_circle_update (text) {
    var coords = text.split (','); // comma-separated list of numbers -> array of strings

    if (coords.length == 2) {
        var c_blue = document.getElementById ("circle_blue"); // in this case, move the blue circle...

        c_blue.setAttribute ("cx", coords[0]);
        c_blue.setAttribute ("cy", coords[1]);
    }
}
function periodic_update () {
    /* In this Circles example, only the blue circle's position needs to be updated periodically
     */
    send_request_query ("circles", "blue_xy", blue_circle_update);
}
function get_started () {
    window.setInterval (periodic_update, 100); // interval in milliseconds

    var stick = document.getElementById ("foreground");

    stick.addEventListener ("mousedown", e_down, false);
    stick.addEventListener ("mouseup",   e_up,   false);
    stick.addEventListener ("mouseover", e_over, false);
    stick.addEventListener ("mousemove", e_move, false);
    stick.addEventListener ("mouseout",  e_out,  false);
}
window.onload = get_started;
