from vispy import scene
from vispy.scene.cameras.perspective import PerspectiveCamera
from vispy.scene.cameras.turntable import TurntableCamera
from vispy.color import Color

import numpy as np

import Space

S = Space.Space()

concrete = {}
concrete['color'] = (1,1,1)

grass = {}
grass['color'] = (0,1,0)

brick = {}
brick['color'] = (1,0,0)

S.add_box([0,0,0],(100,100),0.01,0,concrete)

S.add_box([ 19, 35,0.01],(62,30),1,0,grass)
S.add_box([-35, 19,0.01],(30,62),1,0,grass)
S.add_box([-19,-35,0.01],(62,30),1,0,grass)
S.add_box([ 35,-19,0.01],(30,62),1,0,grass)

S.add_box([0,0,0.01],(20,20),40,30,brick)

# Normal vector towards the sun / light-source
lv_phi = 200 * np.pi / 180
lv_psi =  60 * np.pi / 180
lv = [np.cos(lv_phi)*np.cos(lv_psi),np.sin(lv_phi)*np.cos(lv_psi),np.sin(lv_psi)]

# VisPy scene setup
canvas = scene.SceneCanvas(keys='interactive', size=(1200, 900), show=True)

# Set up a viewbox to display the cube with interactive arcball
view = canvas.central_widget.add_view()
view.bgcolor = '#efefef'
view.camera  = TurntableCamera(scale_factor=120)
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
