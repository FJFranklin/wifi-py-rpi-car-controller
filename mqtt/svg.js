function svg_create_element (str_type, str_id, str_class, str_style, str_transform) {
    var el = document.createElementNS ('http://www.w3.org/2000/svg', str_type);
    if (str_id) {
	el.setAttribute ('id', str_id);
    }
    if (str_class) {
	el.setAttribute ('class', str_class);
    }
    if (str_style) {
	el.setAttribute ('style', str_style);
    }
    if (str_transform) {
	el.setAttribute ('transform', str_transform);
    }
    return el;
}

function svg_create_g (str_id, str_class, str_style, str_transform) {
    var el = svg_create_element ('g', str_id, str_class, str_style, str_transform);
    return el;
}

function svg_create_rect (str_id, str_class, str_style, str_transform, int_x, int_y, int_w, int_h) {
    var el = svg_create_element ('rect', str_id, str_class, str_style, str_transform);
    el.setAttribute ('x',      int_x.toString ());
    el.setAttribute ('y',      int_y.toString ());
    el.setAttribute ('width',  int_w.toString ());
    el.setAttribute ('height', int_h.toString ());
    return el;
}

function svg_create_circle (str_id, str_class, str_style, str_transform, int_cx, int_cy, int_r) {
    var el = svg_create_element ('circle', str_id, str_class, str_style, str_transform);
    el.setAttribute ('cx', int_cx.toString ());
    el.setAttribute ('cy', int_cy.toString ());
    el.setAttribute ('r',  int_r.toString ());
    return el;
}

function svg_create_text (str_id, str_class, str_style, str_transform, int_x, int_y, str_text) {
    var el = svg_create_element ('text', str_id, str_class, str_style, str_transform);
    el.setAttribute ('x', int_x.toString ());
    el.setAttribute ('y', int_y.toString ());
    el.textContent = str_text;
    return el;
}

function svg_matrix_move_and_scale (ox, oy, sx, sy) {
    return "matrix(" + sx.toFixed (3) + ",0,0," + sy.toFixed (3) + "," + ox.toString () + "," + oy.toString () + ")";
}

function svg_rotate (theta) {
    return "rotate(" + theta.toFixed (1) + ")";
}
/*
rect.gauge {
    fill: #111;
}
g.dial rect {
    fill: white;
}
g.dial rect.dial_needle {
    fill: red;
}
circle.dial_pivot {
    fill: black;
    stroke: red;
}
text.label {
    fill: white;
    font-size: 35;
}
*/
function svg_dial_exists (prefix) {
    return null != document.getElementById (prefix + '_main');
}

function svg_dial_create (prefix, x, y, width, height, label_left, label_right) {
    var g_main = svg_create_g (prefix + '_main', null, null, svg_matrix_move_and_scale (x, y, 1, 1));

    var rect_gauge = svg_create_rect (prefix + '_gauge', 'gauge', null, null, 0, 0, width, height);
    g_main.appendChild (rect_gauge);

    var ox = width / 2;
    var oy = height - 10;
    var sx = (width  - 20) / 160;
    var sy = (20 - height) /  80;

    var g_dial = svg_create_g (prefix + '_dial', 'dial', null, svg_matrix_move_and_scale (ox, oy, sx, sy));

    var theta;
    for (theta = -60; theta <= 60; theta += 5) {
	if (theta == 0) {
	    y = 40;
	} else if ((theta == -50) || (theta == 50)) {
	    y = 50;
	} else if ((theta == -25) || (theta == 25)) {
	    y = 60;
	} else {
	    y = 70;
	}
	var rect = svg_create_rect (null, null, null, svg_rotate (theta), -2, y, 4, 80 - y);
	g_dial.appendChild (rect);
    }

    var rect_needle = svg_create_rect (prefix + '_needle', 'dial_needle', null, svg_rotate (5), -1, 0, 2, 80);
    g_dial.appendChild (rect_needle);

    g_main.appendChild (g_dial);

    var circle_pivot = svg_create_circle (prefix + '_pivot', 'dial_pivot', null, null, ox, oy, 5);
    g_main.appendChild (circle_pivot);

    var text_label_L = svg_create_text (prefix + '_label_L', 'label', null, null, 10, height - 10, label_left);
    g_main.appendChild (text_label_L);

    var text_label_R = svg_create_text (prefix + '_label_R', 'label', null, null, width - 10, height - 10, label_right);
    text_label_R.setAttribute ("text-anchor", "end");
    g_main.appendChild (text_label_R);

    return g_main;
}

function svg_gauge_update (prefix, x, y, width, height) {
    var g_main = document.getElementById (prefix + '_main');
    g_main.setAttribute ("transform", svg_matrix_move_and_scale (x, y, 1, 1));

    var rect_gauge = document.getElementById (prefix + '_gauge');
    rect_gauge.setAttribute ("width",  width);
    rect_gauge.setAttribute ("height", height);
}

function svg_dial_update (prefix, x, y, width, height) {
    svg_gauge_update (prefix, x, y, width, height);

    var ox = width / 2;
    var oy = height - 10;
    var sx = (width  - 20) / 160;
    var sy = (20 - height) /  80;

    var g_dial = document.getElementById (prefix + '_dial');
    g_dial.setAttribute ("transform", svg_matrix_move_and_scale (ox, oy, sx, sy));

    var circle_pivot = document.getElementById (prefix + '_pivot');
    circle_pivot.setAttribute ("cx", ox.toString ());
    circle_pivot.setAttribute ("cy", oy.toString ());

    var text_label_L = document.getElementById (prefix + '_label_L');
    text_label_L.setAttribute ("y", (height - 10).toString ());

    var text_label_R = document.getElementById (prefix + '_label_R');
    text_label_R.setAttribute ("x", (width  - 10).toString ());
    text_label_R.setAttribute ("y", (height - 10).toString ());
}

function svg_dial_needle (prefix, theta) {
    var rect_needle = document.getElementById (prefix + '_needle');
    if (rect_needle != null) {
	rect_needle.setAttribute ("transform", svg_rotate (theta));
    }
}
