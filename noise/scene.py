from vispy import scene
from vispy.scene.cameras.turntable import TurntableCamera

import numpy as np

from Noise.Space import Space
from Noise.Material import Material

# Make the scene

S = Space()

sf = 120 # scale factor

case = 1

if case == 1:
    B = S.offset([0,-30,0])

    S.add_box(B.offset([0,44.5,-1]), (100,9), 1, Material.concrete())

    S.add_box(B.offset([0,45,   1]), (100,3), 3, Material.source())
    S.add_box(B.offset([0,40.5, 0]), (100,1), 4, Material.barrier(), (Material.diffzone(), [0,0,0,1]))

    S.add_box(B.offset([  0,  0,0]), (40,40), 1, Material.concrete())

    S.add_box(B.offset([ 19, 30,0]), (62,20), 1, Material.grass())
    S.add_box(B.offset([-35, 14,0]), (30,52), 1, Material.grass())
    S.add_box(B.offset([-19,-35,0]), (62,30), 1, Material.grass())
    S.add_box(B.offset([ 35,-19,0]), (30,62), 1, Material.grass())

    S.add_box(B.offset([ 16,-35,0]), (8,30), 1, Material.concrete())
    S.add_box(B.offset([-35,-16,0]), (30,8), 1, Material.concrete())
    S.add_box(B.offset([ 35, 16,0]), (30,8), 1, Material.concrete())
    S.add_box(B.offset([-16, 30,0]), (8,20), 1, Material.concrete())

    S.add_box(B.rotate_k(-30,[0,0,1]), (20,20), 40, Material.brick(), (Material.diffzone(), [1,1,0,1]))

    # Add a receiver
    l_ear, r_ear = S.make_receiver(B.rotate_k(90, [-20,30,5]), 2, Material.darkzone())

elif case == 2:
    S.add_box(S.offset([0,0,-1]), (100,100), 1, Material.concrete())

    S.add_box(S.rotate_k(45, [0,45,1]), (10,10), 10, Material.source())

    S.add_box(S.rotate_k(30), (20,20), 40, Material.brick(), (Material.diffzone(), [5,5,5,5]))

    S.add_tree(S.offset([20,20,0]), 2, 5, 3)
    S.add_tree(S.offset([30,15,0]), 2, 5, 2)

    # Add a receiver
    l_ear, r_ear = S.make_receiver(S.rotate_k(90, [30,-15,20]), 2, Material.darkzone())

elif case == 3:
    sf = 400

    S.add_box(S.offset([0,0,-1]), (1000,1000), 1, Material.grass())

    S.add_box(S.rotate_k(-27, [190,163,1]), (500,3), 3, Material.source())

    if False:
        S.add_box(S.offset([-288, 232,0]), ( 72,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-288, 196,0]), ( 72,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-288, 172,0]), ( 72,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-288, 136,0]), ( 72,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-288, 112,0]), ( 72,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-288,  76,0]), ( 72,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-288,  52,0]), ( 72,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-288,  16,0]), ( 72,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))

        S.add_box(S.offset([-395, 117,0]), ( 30,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-404,  79,0]), ( 48,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-413,  41,0]), ( 66,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-422,   3,0]), ( 84,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-431, -35,0]), (102,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-440, -73,0]), (120,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-458,-104,0]), ( 84,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([-395,-104,0]), ( 30,8), (5,2), Material.brick(), (Material.diffzone(), [1,1,0,1]))

    if True:
        # Ring 1
        r = 45
        theta_45 = 45 - (6 / (r - 8) * 180 / np.pi) / 2
        d_theta = 7.5 / r * 180 / np.pi
        count = np.int(theta_45 / d_theta)
        angles = theta_45 + d_theta * np.asarray(range(-count,1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 5, Material.concrete())

        angles = 90 + d_theta * np.asarray(range(-count,count+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 5, Material.concrete())

        angles = 180 - theta_45 + d_theta * np.asarray(range(0,count+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 5, Material.concrete())

        # Ring 2
        r = 85
        theta_45 = 45 - (6 / (r - 8) * 180 / np.pi) / 2
        d_theta = 7.5 / r * 180 / np.pi
        count = np.int(theta_45 / d_theta)
        angles = theta_45 + d_theta * np.asarray(range(-count,1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 5, Material.concrete())
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))

        angles = 90 + d_theta * np.asarray(range(-count,count+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 5, Material.concrete())
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))

        angles = 180 - theta_45 + d_theta * np.asarray(range(0,count+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 5, Material.concrete())
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))

        # Ring 3
        r = 120
        theta_45 = 45 - (6 / (r - 8) * 180 / np.pi) / 2
        d_theta = 7.5 / r * 180 / np.pi
        count = np.int(theta_45 / d_theta)
        angles = theta_45 + d_theta * np.asarray(range(-count,1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 5, Material.concrete())

        angles = 90 + d_theta * np.asarray(range(-count,count+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 5, Material.concrete())

        angles = 180 - theta_45 + d_theta * np.asarray(range(0,count+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 5, Material.concrete())

    if True:
        # Ring 4
        r = 160
        theta_45 = 45 - (6 / (r - 8) * 180 / np.pi) / 2
        d_theta = 7.5 / r * 180 / np.pi
        count = np.int(theta_45 / d_theta)

        angles = 90 + d_theta * np.asarray(range(0,count+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 5, Material.concrete())
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))

        angles = 180 - theta_45 + d_theta * np.asarray(range(0,count+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 5, Material.concrete())
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))

        # Ring 5
        r = 190
        theta_45 = 45 - (6 / (r - 8) * 180 / np.pi) / 2
        d_theta = 7.5 / r * 180 / np.pi
        count = int(theta_45 / d_theta)
        c_65 = int(count*20/45)
        theta_65 = 115 - (6 / (r - 8) * 180 / np.pi) / 2

        angles = theta_65 + d_theta * np.asarray(range(0,c_65+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 5, Material.concrete())

        angles = 180 - theta_45 + d_theta * np.asarray(range(0,count+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 5, Material.concrete())

        # Ring 6
        r = 230
        theta_45 = 45 - (6 / (r - 8) * 180 / np.pi) / 2
        d_theta = 7.5 / r * 180 / np.pi
        count = int(theta_45 / d_theta)
        c_65 = int(count*20/45)
        theta_65 = 115 - (6 / (r - 8) * 180 / np.pi) / 2

        angles = theta_65 + d_theta * np.asarray(range(0,c_65+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 5, Material.concrete())
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))

        angles = 180 - theta_45 + d_theta * np.asarray(range(0,count+1))
        S.add_box(S.offset([0,5,0]), ((r-6,angles),4), 5, Material.concrete())
        S.add_box(S.offset([0,5,0]), ((r-2,angles),4), 7.5, Material.concrete(), (Material.diffzone(), [1,1,0,1]))

    # Add a receiver
    l_ear, r_ear = S.make_receiver(S.rotate_k(90, [0,0,2]), 2, Material.darkzone())

elif case == 4:

    basis = S.offset([-5,5,0])
    S.add_box(basis, (10,4), 6, Material.brick(), (Material.diffzone(), [1,1,1,1]))
    
    basis = S.offset([5,5,0])
    S.add_box(basis, (6,8), (5,2), Material.concrete(), (Material.diffzone(), [1,1,0,1]))
    
    S.add_box(S, ((20, [0,10,30,60,100]),8), (7,1), Material.glass(), (Material.diffzone(), [1,1,0,1]))
    
    S.add_box(S, ((20, [270,315]),8), (7,1), Material.barrier(), (Material.diffzone(), [1,1,1,1]))

    S.add_tree(S.offset([-15,5,0]), 2, 5, 3)
    S.add_tree(S.offset([-15,15,0]), 2, 5, 2)

    basis = S.offset([-5,10,0])
    S.add_box(basis, (2,2), 2, Material.source())

    # Add a receiver
    basis = S.rotate_k(90, [0,-5,2])
    l_ear, r_ear = S.make_receiver(basis, 2, Material.darkzone())

search_iterations = 3
print('Left ear: Searching...')
l_ear.search(search_iterations, True)
print('Right ear: Searching...')
r_ear.search(search_iterations, True)

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
