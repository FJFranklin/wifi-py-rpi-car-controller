var client;

var power_options_displayed = true;
var power_options = null;

function power () {
    if (power_options == null) {
	power_options = document.getElementById ("power_options");
    }

    if (power_options_displayed) {
	power_options.style.display = 'none';
	power_options_displayed = false;
    } else {
	power_options.style.display = 'block';
	power_options_displayed = true;
    }
}

function power_car () {
    message = new Paho.Message ("car");
    message.destinationName = "/wifi-py-rpi-car-controller/system/exit";
    client.send (message);
}

function power_controller () {
    message = new Paho.Message ("controller");
    message.destinationName = "/wifi-py-rpi-car-controller/system/exit";
    client.send (message);
}

function mqtt_send_XY (x, y) {
    message = new Paho.Message (x.toFixed (3) + " " + y.toFixed (3));
    message.destinationName = "/wifi-py-rpi-car-controller/dash/XY";
    client.send (message);
}

function mqtt_receive_XY (str) {
    xy_str = str.split (" ");
    x = parseFloat (xy_str[0]);
    y = parseFloat (xy_str[1]);

    var g3_rotate = -60 * y;
    svg_dial_needle ("g3", g3_rotate);

    var g4_rotate = -60 * x;
    svg_dial_needle ("g4", g4_rotate);

    blue_circle (x, y);
}

function user_control (x, y) { // -1 <= x,y <= 1
    var value_x = document.getElementById ("value_x");
    var value_y = document.getElementById ("value_y");

    value_x.innerHTML = x.toFixed (3);
    value_y.innerHTML = y.toFixed (3);

    mqtt_send_XY (x, y);
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

/* Blue circle moves in response to received MQTT data
 */
function blue_circle (x, y) {
    var svg_box = document.getElementById ("foreground");

    var rect = svg_box.getBoundingClientRect ();

    var cx = x * rect.width / 2;
    var cy = y * rect.height / 2;

    var c_blue = document.getElementById ("circle_blue");

    c_blue.setAttribute ("cx", cx.toFixed (3));
    c_blue.setAttribute ("cy", cy.toFixed (3));
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

    svg_gauge_update ("g1", gauge_13_x, gauge_1_y, gauge_width, gauge_height);
    svg_gauge_update ("g2", gauge_24_x, gauge_2_y, gauge_width, gauge_height);

    if (svg_dial_exists ("g3")) {
	svg_dial_update ("g3", gauge_13_x, gauge_3_y, gauge_width, gauge_height);
    } else {
	var g3 = svg_dial_create ("g3", gauge_13_x, gauge_3_y, gauge_width, gauge_height, 'BCK', 'FWD');
	stick.appendChild (g3);
    }
    if (svg_dial_exists ("g4")) {
	svg_dial_update ("g4", gauge_24_x, gauge_4_y, gauge_width, gauge_height);
    } else {
	var g4 = svg_dial_create ("g4", gauge_24_x, gauge_4_y, gauge_width, gauge_height, 'L', 'R');
	stick.appendChild (g4);
    }
}

/* window resize (throttled)
 */
var resize_timeout = 0;

function e_w_resize (event) { // ignore resize events as long as an execution is in the queue
    if (!resize_timeout) {
        resize_timeout = setTimeout (function() {
            resize_timeout = 0;
            window_resize ();
        }, 66); // resize @ 15 fps
    }
}

/* MQTT callbacks
 */
var mqtt_log;

function mqtt_log_update (str) {
    mqtt_log.innerHTML = str;
}

// called when the client connects
function onConnect () {
    // Once a connection has been made, make a subscription and send a message.
    mqtt_log_update ("onConnect");

    client.subscribe ("/wifi-py-rpi-car-controller/car/XY");
}

// called when the client loses its connection
function onConnectionLost (responseObject) {
    if (responseObject.errorCode !== 0) {
	mqtt_log_update ("onConnectionLost:" + responseObject.errorMessage);
    }
}

// called when a message arrives
function onMessageArrived (message) {
    mqtt_log_update ("onMessageArrived:" + message.payloadString);

    if (message.destinationName == "/wifi-py-rpi-car-controller/car/XY") {
	mqtt_receive_XY (message.payloadString);
    }
}

function get_started () {
    var mosquitto_host = window.location.hostname;
    var mosquitto_port = 80; // window.location.port;

    var val_host = document.getElementById ("val_host");
    var val_port = document.getElementById ("val_port");

    val_host.innerHTML = mosquitto_host;
    val_port.innerHTML = mosquitto_port.toString ();

    mqtt_log = document.getElementById ("val_mqtt");

    // Create a client instance
    var client_id = "web-dash-" + Math.random().toString ();    
    client = new Paho.Client (mosquitto_host, Number (mosquitto_port), client_id);

    // set callback handlers
    client.onConnectionLost = onConnectionLost;
    client.onMessageArrived = onMessageArrived;

    // connect the client
    client.connect ({onSuccess:onConnect});

    /* setup event handlers
     */

    var fg = document.getElementById ("foreground");

    /* mouse events
     */
    fg.addEventListener ("mousedown", e_m_down, false);
    fg.addEventListener ("mouseup",   e_m_up,   false);
    fg.addEventListener ("mouseover", e_m_over, false);
    fg.addEventListener ("mousemove", e_m_move, false);
    fg.addEventListener ("mouseout",  e_m_out,  false);

    /* touch events are different from mouse events
     */
    fg.addEventListener ("touchstart",  e_t_start,  false);
    fg.addEventListener ("touchcancel", e_t_cancel, false);
    fg.addEventListener ("touchend",    e_t_end,    false);
    fg.addEventListener ("touchmove",   e_t_move,   false);

    window.addEventListener ('touchmove', function (event) { event.preventDefault () }, false);

    /* finish creating the web interface ...
     */
    power ();
    window_resize ();

    /* ... and handle actual resize events with some intelligence
     */
    resize_timeout = 0;
    window.addEventListener("resize", e_w_resize, false); // throttler code from Mozilla advice
}
window.onload = get_started;
