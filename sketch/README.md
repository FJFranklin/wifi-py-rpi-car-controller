# sketch
Python code for drawing tangent paths in Discovery (previously SpaceClaim) or MatPlotLib

A number of things changed subtly between SpaceClaim v22 and Discovery v252, but I'm gradually getting the code working again. Here's a carcass (based on schematic and measures in Tang et al.) modelled in Discovery 2025 R2.
<img style="align:center;" src="images/Carcass-Tang.png"/>

Left: Straight lines intersecting with optional transition radius. Right: Curved transitions between arcs.
<img style="align:center;" src="images/arc-test-0.png"/>

The same, sketched in SpaceClaim, with automatic detection of closed loops to form surfaces.
<img style="align:center;" src="images/arc-test-0-SpaceClaim.png"/>

Various curved transitions between straight lines and circular arcs.
<img style="align:center;" src="images/arc-test-1.png"/>

The same, sketched in SpaceClaim...
<img style="align:center;" src="images/arc-test-1-SpaceClaim.png"/>

... with automatic detection of closed loops to form surfaces.
<img style="align:center;" src="images/arc-test-1-SpaceClaim-surfaces.png"/>

Outline of a hook using lines, arcs and transitions:
<img style="align:center;" src="images/arc-test-2-hook.png"/>

The hook extruded...
<img style="align:center;" src="images/arc-test-2-hook-SpaceClaim-extruded.png"/>

... with named selections.
<img style="align:center;" src="images/arc-test-2-hook-SpaceClaim-selections.png"/>

It's possible to offset whole paths:
<img style="align:center;width:50%;" src="images/arc-test-8-hook-offsets.png" width="50%" height="50%" />

and to use <a href="https://github.com/nschloe/dmsh">dmsh</a> and <a href="https://github.com/nschloe/optimesh">optimesh</a> to generate meshes:
<img style="align:center;width:50%;" src="images/arc-test-9-hook-mesh.png" />
