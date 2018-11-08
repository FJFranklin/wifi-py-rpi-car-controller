from vispy import scene
from vispy.scene.cameras.turntable import TurntableCamera

import numpy as np

import Space
import Material

# Define the different types of material, etc.

# Surfaces that may contain source points
source = Material.Material((0,1,0,0.5))
source.make_source(0) # reflection; no absorption

# Diffraction surfaces
diffzone = Material.Material((0,0,1,0.1))
diffzone.make_refractive()

# Purely for illustration
darkzone = Material.Material((0,0,0,0.5))
darkzone.make_illustrative()

# Actual materials
concrete = Material.Material((1,1,1,1))
concrete.make_reflective(0.1) # very low absorption

brick = Material.Material((0.8,0.1,0,1))
brick.make_reflective(0.2) # low absorption

barrier = Material.Material((0.1,0.1,0.1,0.5))
barrier.make_reflective(0.9) # high absorption

grass = Material.Material((0,0.8,0,1))
grass.make_reflective(1) # total absorption

# Make the scene

S = Space.Space()

S.add_box([0,0,-1],(100,100),1,0,concrete)

S.add_box([0,45,1],(100,3),3,0,source)

S.add_box([0,41,0],(100,1),4,0,barrier,(diffzone,[0,0,0,0,0,0,0,0,1,0,0,0]))

S.add_box([ 19, 30,0],(62,20),1,0,grass)
S.add_box([-35, 14,0],(30,52),1,0,grass)
S.add_box([-19,-35,0],(62,30),1,0,grass)
S.add_box([ 35,-19,0],(30,62),1,0,grass)

S.add_box([0,0,0],(20,20),40,30,brick,(diffzone,[0,0,0,0,1,1,1,1,1,1,1,1]))
#S.add_box([0,0,0],(20,20),40,30,brick)

# Add a receiver

receiver = S.make_receiver([-20,-20,20],10,darkzone)
receiver.search()

# Display scene

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
