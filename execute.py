# Instructions: Make any changes to the path desired and run this file.

import sys

# SET THIS FOLDER variable to the path of the parent folder that you've downloaded the repository to
# or add to Maya's scripts folder or ensure that the parent folder is added to your PYTHONPATH
folder = '/Maya_LOD_Half_Edge_Mesh/'

#check if folder is part of PYTHONPATH and if not, add it
if folder not in sys.path:
    sys.path.append(folder)

if 'Maya_LOD_Half_Edge_Mesh' in sys.modules:
    del sys.modules['Maya_LOD_Half_Edge_Mesh']
if 'Maya_LOD_Half_Edge_Mesh.half_edge' in sys.modules:
    del sys.modules['Maya_LOD_Half_Edge_Mesh.half_edge']
import Maya_LOD_Half_Edge_Mesh.half_edge

window = Maya_LOD_Half_Edge_Mesh.half_edge.showWindow()
