import pyvista as pv

mesh = pv.read("../output_thick.obj")
texture = pv.read_texture("../output_thick.png")
plotter = pv.Plotter()
plotter.add_mesh(mesh, texture=texture, show_edges=False)
plotter.show()