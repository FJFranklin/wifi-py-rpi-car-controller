function user_control (x, y) { // -1 <= x,y <= 1
    var value_x = document.getElementById ("value_x");
    var value_y = document.getElementById ("value_y");

    value_x.innerHTML = x.toFixed (3);
    value_y.innerHTML = y.toFixed (3);
}

/* Red circle moves in response to button-down events; X & Y values update according to mouse position events
 */
function red_circle (event, bMouse, type) {
    var svg_box = document.getElementById ("foreground");

    var rect = svg_box.getBoundingClientRect ();

    var x = rect.width / 2;
    var y = rect.height / 2;

    if (bMouse) {
	if (event.buttons || event.button) {
	    x = event.clientX - rect.x;
	    y = event.clientY - rect.y;
	}
    } else {
	if ((type == "start") || (type == "move")) {
	    if (event.touches.length) {
		var touch = event.touches[0];
		x = touch.pageX - rect.left;
		y = touch.pageY - rect.top;
	    }
	}
	event.preventDefault ();
	event.stopPropagation ();
    }

    /* Adjust for coordinate system
     */
    x = x - rect.width / 2;
    y = rect.height / 2 - y;

    if (x < -rect.width / 2) {
	x = -rect.width / 2;
    }
    if (y < -rect.height / 2) {
	y = -rect.height / 2;
    }
    if (x > rect.width / 2) {
	x = rect.width / 2;
    }
    if (y > rect.height / 2) {
	y = rect.height / 2;
    }

    var c_red = document.getElementById ("circle_red");

    c_red.setAttribute ("cx", x.toFixed (3));
    c_red.setAttribute ("cy", y.toFixed (3));

    user_control (2 * x / rect.width, 2 * y / rect.height);
}

function e_m_down (event) {
    red_circle (event, true, "down");
}
function e_m_up (event) {
    red_circle (event, true, "up");
}
function e_m_over (event) {
    red_circle (event, true, "over");
}
function e_m_move (event) {
    red_circle (event, true, "move");
}
function e_m_out (event) {
    red_circle (event, true, "out");
}

function e_t_start (event) {
    red_circle (event, false, "start");
}
function e_t_cancel (event) {
    red_circle (event, false, "cancel");
}
function e_t_end (event) {
    red_circle (event, false, "end");
}
function e_t_move (event) {
    red_circle (event, false, "move");
}
	
/* window resize (throttled)
 */
var resize_timeout = 0;

function window_resize () {
    var win = document.defaultView;

    var sw = win.innerWidth  - 20; // dimensions of SVG
    var sh = win.innerHeight - 20;

    var uw = 0; // width of input box

    var bPortrait = true;
    if (sw > sh) {
        bPortrait = false;
    }
    if (bPortrait) {
        var uw_max = sw - 100;
        var uh_max = sh - 300; // allow 200 for other display elements

        if (uw_max < uh_max) {
            uw = uw_max;
        } else {
            uw = uh_max;
        }
    } else {
        var uw_max = sw - 200; // allow 200 for other display elements
        var uh_max = sh - 100;

        if (uw_max < uh_max) {
            uw = uw_max;
        } else {
            uw = uh_max;
        }
    }
    var ox = sw - 50 - uw / 2; // position of input box
    var oy = sh - 50 - uw / 2;

    var stick      = document.getElementById ("stick");
    var control    = document.getElementById ("control");
    var input_zone = document.getElementById ("input_zone");
    var x_axis     = document.getElementById ("x_axis");
    var y_axis     = document.getElementById ("y_axis");
    var foreground = document.getElementById ("foreground");

    stick.setAttribute ("width",  sw.toString ());
    stick.setAttribute ("height", sh.toString ());

    control.setAttribute ("transform", "matrix(1,0,0,-1," + ox.toString () + "," + oy.toString () + ")");

    input_zone.setAttribute ("x", (-uw/2).toString ());
    input_zone.setAttribute ("y", (-uw/2).toString ());
    input_zone.setAttribute ("width",  uw.toString ());
    input_zone.setAttribute ("height", uw.toString ());

    x_axis.setAttribute ("x1", (-uw/2).toString ());
    x_axis.setAttribute ("x2", ( uw/2).toString ());

    y_axis.setAttribute ("y1", (-uw/2).toString ());
    y_axis.setAttribute ("y2", ( uw/2).toString ());

    foreground.setAttribute ("x", (-uw/2).toString ());
    foreground.setAttribute ("y", (-uw/2).toString ());
    foreground.setAttribute ("width",  uw.toString ());
    foreground.setAttribute ("height", uw.toString ());
}
function e_w_resize (event) { // ignore resize events as long as an execution is in the queue
    if (!resize_timeout) {
        resize_timeout = setTimeout (function() {
            resize_timeout = 0;
            window_resize ();
        }, 66); // resize @ 15 fps
    }
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

    stick.addEventListener ("mousedown", e_m_down, false);
    stick.addEventListener ("mouseup",   e_m_up,   false);
    stick.addEventListener ("mouseover", e_m_over, false);
    stick.addEventListener ("mousemove", e_m_move, false);
    stick.addEventListener ("mouseout",  e_m_out,  false);

    stick.addEventListener ("touchstart",  e_t_start,  false);
    stick.addEventListener ("touchcancel", e_t_cancel, false);
    stick.addEventListener ("touchend",    e_t_end,    false);
    stick.addEventListener ("touchmove",   e_t_move,   false);

    window_resize ();
    resize_timeout = 0;
    window.addEventListener("resize", e_w_resize, false); // throttler code from Mozilla advice
}
window.onload = get_started;
