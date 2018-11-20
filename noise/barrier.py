from vispy import scene
from vispy.scene.cameras.turntable import TurntableCamera

import numpy as np

import xlwings as xw

from Noise.Space import Space
from Noise.Material import Material

# Make the source-materials

engine = Material('Engine', (1,0,0,1))
engine.make_source(0,80)

hvac = Material('HVAC', (0,0,1,1))
hvac.make_source(0,30)

wheel = Material('Wheel', (0.75,0.75,0.75,1))
wheel.make_source(0,50)

rail = Material('Rail', (0.25,0.25,0.25,1))
rail.make_source(0,50)

# Note: Rolling Noise: Lp = Lp0 + 30 log10 (V / V0), where Lp0 is the noise level at the speed V0
#       [https://www.southampton.ac.uk/engineering/research/groups/dynamics/rail/rolling_railway_noise.page]

def add_vehicle(space, basis):
    space.add_box(basis.offset([ 0,   0,    1    ]), (20,   3   ), 3,    Material.glass(), (Material.diffzone(), [0,0,0.25,0.25]))
    space.add_box(basis.offset([ 0,   0,    4    ]), ( 2,   2   ), 0.25, hvac)
    space.add_box(basis.offset([ 0,   0,    0.5  ]), ( 2,   2   ), 0.5,  engine)
    space.add_box(basis.offset([-8,  -0.75, 0    ]), ( 8,   0.25), 0.25, rail)
    space.add_box(basis.offset([-8,   0.75, 0    ]), ( 8,   0.25), 0.25, rail)
    space.add_box(basis.offset([ 8,  -0.75, 0    ]), ( 8,   0.25), 0.25, rail)
    space.add_box(basis.offset([ 8,   0.75, 0    ]), ( 8,   0.25), 0.25, rail)
    space.add_box(basis.offset([-9.5,-0.75, 0.25 ]), ( 0.75,0.25), 0.75, wheel)
    space.add_box(basis.offset([-6.5,-0.75, 0.25 ]), ( 0.75,0.25), 0.75, wheel)
    space.add_box(basis.offset([-9.5, 0.75, 0.25 ]), ( 0.75,0.25), 0.75, wheel)
    space.add_box(basis.offset([-6.5, 0.75, 0.25 ]), ( 0.75,0.25), 0.75, wheel)
    space.add_box(basis.offset([ 9.5,-0.75, 0.25 ]), ( 0.75,0.25), 0.75, wheel)
    space.add_box(basis.offset([ 6.5,-0.75, 0.25 ]), ( 0.75,0.25), 0.75, wheel)
    space.add_box(basis.offset([ 9.5, 0.75, 0.25 ]), ( 0.75,0.25), 0.75, wheel)
    space.add_box(basis.offset([ 6.5, 0.75, 0.25 ]), ( 0.75,0.25), 0.75, wheel)

def dB_get(totals, label):
    if label in totals:
        value = totals[label]
    else:
        value = 0
    return value

# Setup the spreadsheet

wb = xw.Book()

gs = wb.sheets.add('Ground')
gs[0, 0].value = 'Barrier Height'
gs[0, 1].value = 'Left Total'
gs[0, 2].value = 'Engine'
gs[0, 3].value = 'HVAC'
gs[0, 4].value = 'Rails'
gs[0, 5].value = 'Wheels'
gs[0, 6].value = 'Right Total'
gs[0, 7].value = 'Engine'
gs[0, 8].value = 'HVAC'
gs[0, 9].value = 'Rails'
gs[0,10].value = 'Wheels'

ws = wb.sheets.add('Window')
ws[0, 0].value = 'Barrier Height'
ws[0, 1].value = 'Left Total'
ws[0, 2].value = 'Engine'
ws[0, 3].value = 'HVAC'
ws[0, 4].value = 'Rails'
ws[0, 5].value = 'Wheels'
ws[0, 6].value = 'Right Total'
ws[0, 7].value = 'Engine'
ws[0, 8].value = 'HVAC'
ws[0, 9].value = 'Rails'
ws[0,10].value = 'Wheels'

wb.save('test.xlsx')

row = 1

sf = 120 # scale factor for final view

search_iterations = 6
drop_if = 0.999
show_projections = True

# Make the scene

for h in range(1, 6):
    S = Space()

    B = S.offset([0,-30,0])

    S.add_box(B.offset([ 0,52,  -1]), (100, 24), 1, Material.concrete())
    S.add_box(B.offset([ 0,40.5, 0]), (100,  1), h, Material.barrier(), (Material.diffzone(), [0,0,0,0.5]))
    S.add_box(B.offset([ 0,53.5, 0]), (100,  1), h, Material.barrier(), (Material.diffzone(), [0,0,0,0.5]))

    S.add_box(B.offset([  0,  0, 0]), ( 40, 40), 1, Material.concrete())

    S.add_box(B.offset([ 19, 30, 0]), ( 62, 20), 1, Material.grass())
    S.add_box(B.offset([-35, 14, 0]), ( 30, 52), 1, Material.grass())
    S.add_box(B.offset([-19,-35, 0]), ( 62, 30), 1, Material.grass())
    S.add_box(B.offset([ 35,-19, 0]), ( 30, 62), 1, Material.grass())

    S.add_box(B.offset([ 16,-35, 0]), (  8, 30), 1, Material.concrete())
    S.add_box(B.offset([-35,-16, 0]), ( 30,  8), 1, Material.concrete())
    S.add_box(B.offset([ 35, 16, 0]), ( 30,  8), 1, Material.concrete())
    S.add_box(B.offset([-16, 30, 0]), ( 8,  20), 1, Material.concrete())

    S.add_box(B.rotate_k(-30,[0,0,1]), (20,20), 40, Material.brick(), (Material.diffzone(), [1,1,0,1]))

    add_vehicle(S, B.offset([-19,49,0]))

    # Add receivers

    print('=== Window ===')
    w_l_ear, w_r_ear = S.make_receiver(B.rotate_k(-30,[0,0,1]).rotate_k(90,[0,10.5,30]), 2)
    print('Left ear: Searching...')
    w_l_sources = w_l_ear.search(search_iterations, drop_if, show_projections)
    print('Right ear: Searching...')
    w_r_sources = w_r_ear.search(search_iterations, drop_if, show_projections)
    print('Left ear: Calculating...')
    w_l_totals = w_l_ear.calc()
    print('Right ear: Calculating...')
    w_r_totals = w_r_ear.calc()

    ws[row, 0].value = h

    ws[row, 1].value = dB_get(w_l_totals, 'total')
    ws[row, 2].value = dB_get(w_l_totals, 'Engine')
    ws[row, 3].value = dB_get(w_l_totals, 'HVAC')
    ws[row, 4].value = dB_get(w_l_totals, 'Rail')
    ws[row, 5].value = dB_get(w_l_totals, 'Wheel')

    ws[row, 6].value = dB_get(w_r_totals, 'total')
    ws[row, 7].value = dB_get(w_r_totals, 'Engine')
    ws[row, 8].value = dB_get(w_r_totals, 'HVAC')
    ws[row, 9].value = dB_get(w_r_totals, 'Rail')
    ws[row,10].value = dB_get(w_r_totals, 'Wheel')

    print('=== Ground ===')
    g_l_ear, g_r_ear = S.make_receiver(B.rotate_k(90, [-20,30,2]), 2)
    print('Left ear: Searching...')
    g_l_sources = g_l_ear.search(search_iterations, drop_if, show_projections)
    print('Right ear: Searching...')
    g_r_sources = g_r_ear.search(search_iterations, drop_if, show_projections)
    print('Left ear: Calculating...')
    g_l_totals = g_l_ear.calc()
    print('Right ear: Calculating...')
    g_r_totals = g_r_ear.calc()

    gs[row, 0].value = h

    gs[row, 1].value = dB_get(g_l_totals, 'total')
    gs[row, 2].value = dB_get(g_l_totals, 'Engine')
    gs[row, 3].value = dB_get(g_l_totals, 'HVAC')
    gs[row, 4].value = dB_get(g_l_totals, 'Rail')
    gs[row, 5].value = dB_get(g_l_totals, 'Wheel')

    gs[row, 6].value = dB_get(g_r_totals, 'total')
    gs[row, 7].value = dB_get(g_r_totals, 'Engine')
    gs[row, 8].value = dB_get(g_r_totals, 'HVAC')
    gs[row, 9].value = dB_get(g_r_totals, 'Rail')
    gs[row,10].value = dB_get(g_r_totals, 'Wheel')

    row += 1
    #wb.save()

# Finished collecting data now; close the spreadsheet
#wb.close()

# Display scene

# Normalised vector towards the sun / light-source
lv_phi = 200 * np.pi / 180
lv_psi =  60 * np.pi / 180
lv = [np.cos(lv_phi)*np.cos(lv_psi),np.sin(lv_phi)*np.cos(lv_psi),np.sin(lv_psi)]

# VisPy scene setup
canvas = scene.SceneCanvas(keys='interactive', size=(1200, 900), show=True)

# Set up a viewbox to display the cube with interactive arcball
view = canvas.central_widget.add_view()
view.bgcolor = '#efefef'
view.camera  = TurntableCamera(scale_factor=sf)
view.padding = 10

for p in S.polygons:
    v, c = p.vertices()
    f, e = p.get_colors(lv, 0.7)
    if f is not None:
        scene.visuals.Mesh(vertices=v, faces=range(0,c), color=f, mode='triangle_fan', parent=view.scene)
    if e is not None:
        scene.visuals.Mesh(vertices=v, faces=range(0,c), color=e, mode='lines', parent=view.scene)

# & go...
canvas.app.run()
