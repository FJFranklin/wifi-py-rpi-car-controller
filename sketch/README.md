# sketch
Python code for drawing tangent paths in SpaceClaim or MatPlotLib

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

and to use <a href="https://github.com/nschloe/dmsh">dmsh</a> to generate meshes:
<img style="align:center;width:50%;" src="images/arc-test-9-hook-mesh.png" width="50%" height="50%" />
