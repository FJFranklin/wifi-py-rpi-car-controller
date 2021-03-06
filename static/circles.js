function user_control (x, y) { // -1 <= x,y <= 1
    var value_x = document.getElementById ("value_x");
    var value_y = document.getElementById ("value_y");

    value_x.innerHTML = x.toFixed (3);
    value_y.innerHTML = y.toFixed (3);

    var g3_needle = document.getElementById ("g3_needle");
    var g3_rotate = -60 * y;

    g3_needle.setAttribute ("transform", "rotate(" + g3_rotate.toFixed (1) + ")");

    var g4_needle = document.getElementById ("g4_needle");
    var g4_rotate = -60 * x;

    g4_needle.setAttribute ("transform", "rotate(" + g4_rotate.toFixed (1) + ")");
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

function redraw_gauges (width, height) {
    var ox = width / 2;
    var oy = height - 10;
    var sx = (width  - 20) / 160;
    var sy = (20 - height) /  80;

    var g3_dial    = document.getElementById ("g3_dial");
    var g3_pivot   = document.getElementById ("g3_pivot");
    var g3_label_L = document.getElementById ("g3_label_L");
    var g3_label_R = document.getElementById ("g3_label_R");

    g3_dial.setAttribute ("transform", "matrix(" + sx.toFixed (3) + ",0,0," + sy.toFixed (3) + "," +
			  ox.toString () + "," + oy.toString () + ")");

    g3_pivot.setAttribute ("cx", ox.toString ());
    g3_pivot.setAttribute ("cy", oy.toString ());

    g3_label_L.setAttribute ("y", (height - 10).toString ());
    g3_label_R.setAttribute ("y", (height - 10).toString ());
    g3_label_R.setAttribute ("x", (width  - 10).toString ());

    var g4_dial    = document.getElementById ("g4_dial");
    var g4_pivot   = document.getElementById ("g4_pivot");
    var g4_label_L = document.getElementById ("g4_label_L");
    var g4_label_R = document.getElementById ("g4_label_R");

    g4_dial.setAttribute ("transform", "matrix(" + sx.toFixed (3) + ",0,0," + sy.toFixed (3) + "," +
			  ox.toString () + "," + oy.toString () + ")");

    g4_pivot.setAttribute ("cx", ox.toString ());
    g4_pivot.setAttribute ("cy", oy.toString ());

    g4_label_L.setAttribute ("y", (height - 10).toString ());
    g4_label_R.setAttribute ("y", (height - 10).toString ());
    g4_label_R.setAttribute ("x", (width  - 10).toString ());
}
function window_resize () {
    var win = document.defaultView;

    var sw = win.innerWidth  - 20; // dimensions of SVG
    var sh = win.innerHeight - 20;

    var uw = 0; // width of input box

    var gx = 50; // gauge zone
    var gy = 50;
    var gw = 0;
    var gh = 0;

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
	gw = uw_max;
	gh = sh - 120 - uw;
    } else {
        var uw_max = sw - 200; // allow 200 for other display elements
        var uh_max = sh - 100;

        if (uw_max < uh_max) {
            uw = uw_max;
        } else {
            uw = uh_max;
        }
	gw = sw - 120 - uw;
	gh = uh_max;
    }
    var ox = sw - 50 - uw / 2; // position of input box
    var oy = sh - 50 - uw / 2;

    var gauge_13_x = gx;
    var gauge_24_x = 0;

    var gauge_1_y = gy;
    var gauge_2_y = 0;
    var gauge_3_y = 0;
    var gauge_3_y = 0;

    var gauge_width  = 0;
    var gauge_height = 0;

    if (gw > gh) { // gauge zone is landscape
	gauge_width  = (gw - 20) / 2;
	gauge_height = (gh - 20) / 2;

	gauge_24_x = gauge_13_x + 20 + gauge_width;

	gauge_2_y  = gauge_1_y;
	gauge_3_y  = gauge_1_y  + 20 + gauge_height;
	gauge_4_y  = gauge_3_y;
    } else {       // gauge zone is portrait
	gauge_width  = gw;
	gauge_height = (gh - 60) / 4;

	gauge_24_x = gauge_13_x;

	gauge_2_y  = gauge_1_y  + 20 + gauge_height;
	gauge_3_y  = gauge_2_y  + 20 + gauge_height;
	gauge_4_y  = gauge_3_y  + 20 + gauge_height;
    }

    var stick      = document.getElementById ("stick");
    var control    = document.getElementById ("control");
    var input_zone = document.getElementById ("input_zone");
    var x_axis     = document.getElementById ("x_axis");
    var y_axis     = document.getElementById ("y_axis");
    var foreground = document.getElementById ("foreground");
    var gauge_1    = document.getElementById ("gauge_1");
    var gauge_2    = document.getElementById ("gauge_2");
    var gauge_3    = document.getElementById ("gauge_3");
    var gauge_4    = document.getElementById ("gauge_4");
    var gauge_1r   = document.getElementById ("gauge_1r");
    var gauge_2r   = document.getElementById ("gauge_2r");
    var gauge_3r   = document.getElementById ("gauge_3r");
    var gauge_4r   = document.getElementById ("gauge_4r");
    var net_qual   = document.getElementById ("net_qual");

    stick.setAttribute ("width",  sw.toString ());
    stick.setAttribute ("height", sh.toString ());

    control.setAttribute ("transform", "matrix(1,0,0,-1," + ox.toString () + "," + oy.toString () + ")");

    net_qual.setAttribute ("transform", "matrix(0," + (uw / 200).toString () + ",2.5,0," + (uw / 2).toString () + ",0)");

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

    gauge_1.setAttribute ("transform", "matrix(1,0,0,1," + gauge_13_x.toString () + "," + gauge_1_y.toString () + ")");
    gauge_2.setAttribute ("transform", "matrix(1,0,0,1," + gauge_24_x.toString () + "," + gauge_2_y.toString () + ")");
    gauge_3.setAttribute ("transform", "matrix(1,0,0,1," + gauge_13_x.toString () + "," + gauge_3_y.toString () + ")");
    gauge_4.setAttribute ("transform", "matrix(1,0,0,1," + gauge_24_x.toString () + "," + gauge_4_y.toString () + ")");

    gauge_1r.setAttribute ("width",  gauge_width.toString ());
    gauge_1r.setAttribute ("height", gauge_height.toString ());

    gauge_2r.setAttribute ("width",  gauge_width.toString ());
    gauge_2r.setAttribute ("height", gauge_height.toString ());

    gauge_3r.setAttribute ("width",  gauge_width.toString ());
    gauge_3r.setAttribute ("height", gauge_height.toString ());

    gauge_4r.setAttribute ("width",  gauge_width.toString ());
    gauge_4r.setAttribute ("height", gauge_height.toString ());

    redraw_gauges (gauge_width, gauge_height);
}
function e_w_resize (event) { // ignore resize events as long as an execution is in the queue
    if (!resize_timeout) {
        resize_timeout = setTimeout (function() {
            resize_timeout = 0;
            window_resize ();
        }, 66); // resize @ 15 fps
    }
}

function update_net_quality (delta_tick) {
    var nq0 = document.getElementById ("nq0");
    var nq1 = document.getElementById ("nq1");
    var nq2 = document.getElementById ("nq2");
    var nq3 = document.getElementById ("nq3");
    var nq4 = document.getElementById ("nq4");
    var nq5 = document.getElementById ("nq5");
    var nq6 = document.getElementById ("nq6");
    var nq7 = document.getElementById ("nq7");
    var nq8 = document.getElementById ("nq8");
    var nq9 = document.getElementById ("nq9");

    if (delta_tick <= 1) {
	nq0.setAttribute ("class", "nq_good");
    } else {
	nq0.setAttribute ("class", "nq_none");
    }
    if (delta_tick <= 2) {
	nq1.setAttribute ("class", "nq_good");
    } else {
	nq1.setAttribute ("class", "nq_none");
    }
    if (delta_tick <= 3) {
	nq2.setAttribute ("class", "nq_good");
    } else {
	nq2.setAttribute ("class", "nq_none");
    }
    if (delta_tick <= 4) {
	nq3.setAttribute ("class", "nq_good");
    } else {
	nq3.setAttribute ("class", "nq_none");
    }
    if (delta_tick <= 5) {
	nq4.setAttribute ("class", "nq_good");
    } else {
	nq4.setAttribute ("class", "nq_none");
    }
    if (delta_tick <= 6) {
	nq5.setAttribute ("class", "nq_good");
    } else {
	nq5.setAttribute ("class", "nq_none");
    }
    if (delta_tick <= 7) {
	nq6.setAttribute ("class", "nq_good");
    } else {
	nq6.setAttribute ("class", "nq_none");
    }
    if (delta_tick <= 8) {
	nq7.setAttribute ("class", "nq_good");
    } else {
	nq7.setAttribute ("class", "nq_none");
    }
    if (delta_tick <= 9) {
	if (delta_tick <= 8) {
	    nq8.setAttribute ("class", "nq_good");
	} else {
	    nq8.setAttribute ("class", "nq_bad");
	}
    } else {
	nq8.setAttribute ("class", "nq_none");
    }
    if (delta_tick <= 10) {
	if (delta_tick <= 8) {
	    nq9.setAttribute ("class", "nq_good");
	} else {
	    nq9.setAttribute ("class", "nq_bad");
	}
    } else {
	nq9.setAttribute ("class", "nq_none");
    }
    if (delta_tick > 10) {
	if (delta_tick % 20 < 10) {
	    nq0.setAttribute ("class", "nq_none");
	    nq1.setAttribute ("class", "nq_none");
	    nq2.setAttribute ("class", "nq_none");
	    nq3.setAttribute ("class", "nq_none");
	    nq4.setAttribute ("class", "nq_none");
	    nq5.setAttribute ("class", "nq_none");
	    nq6.setAttribute ("class", "nq_none");
	    nq7.setAttribute ("class", "nq_none");
	    nq8.setAttribute ("class", "nq_none");
	    nq9.setAttribute ("class", "nq_none");
	} else {
	    nq0.setAttribute ("class", "nq_bad");
	    nq1.setAttribute ("class", "nq_bad");
	    nq2.setAttribute ("class", "nq_bad");
	    nq3.setAttribute ("class", "nq_bad");
	    nq4.setAttribute ("class", "nq_bad");
	    nq5.setAttribute ("class", "nq_bad");
	    nq6.setAttribute ("class", "nq_bad");
	    nq7.setAttribute ("class", "nq_bad");
	    nq8.setAttribute ("class", "nq_bad");
	    nq9.setAttribute ("class", "nq_bad");
	}
    }
}

var tick_last_response = 0;
var tick = 0;

/* Asynchronous request from server, sending and receiving text
 * 
 * (Take a look at https://www.html5rocks.com/en/tutorials/file/xhr2/ for getting binary data, e.g., images)
 */
function send_request_query (str_name_namespace, str_value_query, callback_function) {
    var query = new XMLHttpRequest ();

    query.open ("GET", "/query?name=" + str_name_namespace + "&value=" + str_value_query);
    query.responseType = "text";
    query.onload = function (e) {
	tick_last_response = tick;
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

    update_net_quality (tick - tick_last_response);
    tick = tick + 1;
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
