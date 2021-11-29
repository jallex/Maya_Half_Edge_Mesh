import maya.api.OpenMaya as OpenMaya

# Instructions: to start tool, navigate to execute_tool.py and run the file

from PySide2.QtCore import * 
from PySide2.QtGui import *
from PySide2.QtUiTools import *
from PySide2.QtWidgets import *
from functools import partial
import maya.cmds as cmds
from maya import OpenMayaUI
from pathlib import Path
from shiboken2 import wrapInstance

class CurrentPM:
    def __init__(self):
        self.object = None
        
#show gui window
def showWindow():
    # get this files location so we can find the .ui file in the /ui/ folder alongside it
    UI_FILE = str(Path(__file__).parent.resolve() / "pm_ui.ui")
    loader = QUiLoader()
    file = QFile(UI_FILE)
    file.open(QFile.ReadOnly)
     
    #Get Maya main window to parent gui window to it
    mayaMainWindowPtr = OpenMayaUI.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(int(mayaMainWindowPtr), QWidget)
    ui = loader.load(file, parentWidget=mayaMainWindow)
    file.close()
    
    ui.setParent(mayaMainWindow)
    ui.setWindowFlags(Qt.Window)
    ui.setWindowTitle('Progressive Mesh')
    ui.setObjectName('Progressive Mesh')
    ui.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

    this_PM = CurrentPM()

#Close dialog
    def spinbox_changed(num_edges_requested):
        he_data = maya_to_heMesh(this_PM.object)

        current_num_edges = he_data.num_edges
        this_he = he_data.halfEdge 
        count = 0

        #print("current_num_edges", current_num_edges)
        #print("num_edges_requested", num_edges_requested)
        if(current_num_edges > num_edges_requested):
            # Reduce edges with edge collapse
            difference = current_num_edges - num_edges_requested
            #must reduce by a multiple of 3
            if difference % 3 == 0:
                new_he = reduce_many_he(this_he, difference, current_num_edges)
                heMesh_to_maya(new_he)
            else:
                difference = difference + (3 - (difference % 3))
                ui.spinBox_num_edges.setValue(current_num_edges - difference)
            #ui.spinBox_num_edges.setMaximum(new_he.num_edges)

        # hack-y way of finding a half edge with a twin
        while(True):
            if not this_he.twin == None:
                new_he =  this_he
                break
            else:
                this_he = this_he.next
            if count >=5:
                new_he = this_he
                break

        if(current_num_edges < num_edges_requested):
            # Increase edges with vertex split
            pass

        if not (ui.spinBox_num_edges.value() == ui.horizontalSlider_num_edges.value()):
            # Update horizontal slider
            ui.horizontalSlider_num_edges.setValue(new_he.num_edges)
        pass

    def slider_released():
        if not (ui.spinBox_num_edges.value() == ui.horizontalSlider_num_edges.value()):
            ui.spinBox_num_edges.setValue(ui.horizontalSlider_num_edges.value())
        #ui.horizontalSlider_num_edges.setMaximum(he_data.num_edges)

    def slider_changed(num_edges_requested):
        #ui.spinBox_num_edges.setValue(ui.horizontalSlider_num_edges.value())
        pass

    def set_selected_button_pressed():
        #get selected object
        selected_object = OpenMaya.MGlobal.getActiveSelectionList(0)
        he_data = maya_to_heMesh(selected_object)
        this_PM.object = he_data

        #Update number of edges on slider and dialog to be the max
        ui.horizontalSlider_num_edges.setMaximum(he_data.num_edges)
        ui.spinBox_num_edges.setMaximum(he_data.num_edges)
        ui.horizontalSlider_num_edges.setValue(he_data.num_edges)
        ui.spinBox_num_edges.setValue(he_data.num_edges)

        #Update text on UI for object name
        selected = cmds.ls(sl=True,long=True) or []
        if not(len(selected) == 1):
            print("Please set center to be exactly 1 selected object.")
        else: 
            selected_name = selected[0]
        
        text = "Selected Mesh: " + (str(selected_name[1:]))
        #change ui text
        ui.selected_mesh_text.setText(text)

    #connect buttons to functions
    ui.spinBox_num_edges.valueChanged.connect(partial(spinbox_changed))
    #reduce 3 edges at a time with one edge collapse
    #ui.spinBox.setSingleStep(3)
    ui.horizontalSlider_num_edges.sliderReleased.connect(partial(slider_released))
    ui.horizontalSlider_num_edges.valueChanged.connect(partial(slider_changed))
    #ui.horizontalSlider_num_edges.setSingleStep(3)
    ui.select_button.clicked.connect(partial(set_selected_button_pressed))
     
    # show the QT ui
    ui.show()
    return ui

if __name__ == "__main__":
    window=showWindow()

#Classes and methods representing the half edge data structure

#Vertex data
class Vertex:
  def __init__(self, x, y, z, id):
      self.x = x
      self.y = y
      self.z = z
      self.id = id

#Edge data
class Edge:
  def __init__(self):
      self.vert1 = None
      self.vert2 = None
      self.id = None
  def __init__(self, vert1, vert2, id):
      self.vert1 = vert1
      self.vert2 = vert2
      self.id = id

#Face data
class Face:
  def __init__(self):
      #starting half-edge
      self.start_edge = None
      self.id = None
      #vertices on this face
      self.verts = []
      #edges on this face
      self.edges = []

#HalfEdge data
class HalfEdge:
  def __init__(self):
      self.face = None
      self.end_vert = None
      self.next = None
      self.twin = None
      self.id = None
      self.edge = None

   #set half edge data
  def set(self, face, vert, next, twin, id, edge):
      #face that this halfEdge is a part of
      self.face = face
      #he Vertex between this HalfEdge and the next HalfEdge in the ring.
      self.vert = vert
      #the next HalfEdge in the loop of HalfEdges that make up this HalfEdge's Face.
      self.next = next
      #twin points to the HalfEdge that lies parallel to this HalfEdge and which travels in the opposite direction ans is part of an adjacent Face
      self.twin = twin
      #unique integer ID
      self.id = id
      #the edge it's on
      self.edge = edge

#HalfEdge Mesh data
class HalfEdgeMesh:
  def __init__(self, halfEdge):
      self.halfEdge = halfEdge
      self.last_mesh = None
      self.num_edges = None

#Reduce multiple edges, number of edges to reduce specified by num_edges param
def reduce_many_he(he, num_edges, current_edges):
    count = 0
    old_he = he

    #ensure we have enough edges to reduce
    if num_edges >= current_edges:
        num_edges = current_edges - 1
        
    while(True):
        if not he.twin == None:
            he = reduce_he(he.twin)
            count += 3
        elif not he.next.twin.next == None: 
            he = reduce_he(he.next.twin.next)
            count += 3
        if count >= num_edges:
            print("reduced ", count, "edges")
            break
    new_he_mesh = HalfEdgeMesh(he)
    new_he_mesh.last_mesh = HalfEdgeMesh(old_he)
    new_he_mesh.num_edges = current_edges - count
    return new_he_mesh

#Reduce one given half edge using edge collapse
def reduce_he(halfedge):
   """
 
   Reduce the given half edge mesh by the given percentage.
  
   :returns: :class:'HalfEdgeMesh' the reduced half edge mesh.
   """
   #half edge to reduce
   deleting_edges = set()
   deleting_edges.add(halfedge)
   deleting_edges.add(halfedge.twin)

   he = halfedge
   start_he = halfedge

   vert1 = halfedge.vert
   vert2 = halfedge.twin.vert
   vert1_id = vert1.id
   vert2_id = vert2.id

   x = (vert1.x + vert2.x)/2.0
   y = (vert1.y + vert2.y)/2.0
   z = (vert1.z + vert2.z)/2.0

   new_vertex = Vertex(x,y,z,vert1_id)

   f1e1 = halfedge.next
   f1e2 = halfedge.next.next

   f2e1 = halfedge.twin.next
   f2e2 = halfedge.twin.next.next

   twins = []

   #set new twins
   twin1 = f1e1.twin
   twin2 = f1e2.twin
   twin1.twin=twin2
   twin2.twin=twin1

   twins.append(twin1) 
   twins.append(twin2) 

   twin1 = f2e1.twin
   twin2 = f2e2.twin
   twin1.twin=twin2
   twin2.twin=twin1

   twins.append(twin1) 
   twins.append(twin2) 

   #iterate around verts to change references to previous vert
   for e in twins:
       if (e.vert.id == vert1_id or e.vert.id == vert2_id):
           e.vert = new_vertex

#    Attempt at updating verts only in surrounding area, as opposed to checking whole mesh
#    for e in twins:
#         start_he = e
#         temp_he = e
#         #While we haven't seen the original halfEdge, iterate through each face
#         while(True):
#             start_he2 = temp_he
#             temp_he2 = temp_he
#             #while we haven't seen the original halfEdge, iterate through  vertices on this face
#             while(True):
#                 print("temp_he2 vert", temp_he2.vert.id)
#                 if(temp_he2.vert.id == vert1_id or temp_he2.vert.id == vert2_id):
#                     temp_he2.vert = new_vertex
#                 count += 1
#                 print("checked", count, "edges")
#                 #go to next half edge on this face
#                 temp_he2 = temp_he2.next
#                 if(temp_he2.id == start_he2.id):
#                     break
#             #go to next face
#             temp_he = temp_he.next.twin
#             if(temp_he.id == start_he.id):
#                 break  


   #Iterate around entire half edge mesh and update deleted vertice references
   #starting halfEdge
   start_he = halfedge
   he = halfedge
   he_set = {he}
   seen_set = {he.id}
    #iterate through all vertices on mesh
   while(True):
      if len(he_set) == 0:
          break
      else:
          he = he_set.pop()
      start_he = he
      #while we haven't seen the original halfEdge, iterate through vertices on this face
      while(True):
           #get all vertice positions of this face
           this_vertex_id = he.vert.id
           if(this_vertex_id == vert1_id or this_vertex_id == vert2_id):
               he.vert = new_vertex

           #find other faces to traverse around
           if not he.twin == None:
               if he.twin.id not in seen_set:
                   he_set.add(he.twin)
 
           #go to next half edge on this face
           he = he.next
           seen_set.add(he.id)
             
           #reached start
           if(he.id == start_he.id):
               break
   #print("num_edges after one reduce", len(seen_set)/2)
   #new_hemesh = HalfEdgeMesh(he)
   return he

def maya_to_heMesh(selected_object):
  """
  Convert the selected object in Maya to a half edge mesh.
   :returns: :class:'HalfEdgeMesh' the selected object as a half edge mesh data structure.
  """
  #get first selected object
  #selected_object = OpenMaya.MGlobal.getActiveSelectionList(0)
  selected_object = OpenMaya.MGlobal.getActiveSelectionList(0)
  dag = selected_object.getDagPath(0)
  poly = OpenMaya.MItMeshPolygon(dag)
  vert_It= OpenMaya.MItMeshVertex(dag)
  edge_list = []
  face_list = []
  half_edge_list = []
  edges_verts = []
  vert_list = []
  #Get vertex indices and locations
  while not vert_It.isDone():
      index = vert_It.index()
      position = vert_It.position()
      new_vert = Vertex(position[0], position[1], position[2], index)
      vert_list.append(new_vert)
      vert_It.next()
  #Iterate through each face of the poly
  while not poly.isDone():
      face = poly.index()
      #get verts on face in winding order
      face_verts = poly.getVertices()
      #list of edges by vertices
      for index, vert in enumerate(face_verts):
           if index != len(face_verts) - 1:
               edges_verts.append([vert, face_verts[index + 1]])
           else:
               edges_verts.append([vert, face_verts[0]])
    
      #create face
      face = Face()
      face.verts = face_verts
      face_list.append(face)
      edges_on_this_face = []
      half_edges_on_this_face = []
      poly.next()
  edge_count = 0

  #Create edges and half-edges
  for index, edge in enumerate(edges_verts):
      #vertices are in order that the half-edge should be facing
      this_edge = Edge(edge[0], edge[1], index)
      #find if pre-existing edge exists
      for e in edge_list:
          if (e.vert1 == edge[0] and e.vert2 == edge[1]) or (e.vert1 == edge[1] and e.vert2 == edge[0]):
              this_edge = e
              #print("this edge is shared:", e.id, "verts:", e.vert1,e.vert2, "edge:", edge, )
      edge_list.append(this_edge)
      edges_on_this_face.append(this_edge)
      #Create half-edge
      half_edge = HalfEdge()
      half_edge.edge = this_edge
      half_edge.face = face
      #set half_edge's vert
      vert = vert_list[edge[0]]
      half_edge.vert = vert
       #keep track of half_edges on this face
      half_edges_on_this_face.append(half_edge)
      if edge_count == 2:
          #set first which we skipped
          half_edge_list[index - 2].next = half_edge_list[index - 1]
          #set middle
          half_edge_list[index - 1].next = half_edge
          #set last
          half_edge.next = half_edge_list[index - 2]
          edge_count = 0
      else:
          edge_count += 1
      #done setting nexts
      half_edge_list.append(half_edge)
      face.edges = half_edges_on_this_face
  #edges seen so far used in the assignment of twins
  edges_seen = {}
   #Assigning twins
  for index, half_edge in enumerate(half_edge_list):
      #set id
      half_edge.id = index
      #assign twins
      if half_edge.edge.id in edges_seen.keys():
          half_edge_list[edges_seen[half_edge.edge.id]].twin = half_edge
          half_edge.twin = half_edge_list[edges_seen[half_edge.edge.id]]
      else:
          #edge index : half edge index
          edges_seen[half_edge.edge.id] = half_edge.id
  #Create Half Edge Mesh
  half_edge_mesh = HalfEdgeMesh(half_edge_list[0])
  # print("edges according to HE list", len(half_edge_list) / 2)
  half_edge_mesh.num_edges = len(half_edge_list) / 2

#   print("HALF EDGE DATA")
#   for index, half_edge in enumerate(half_edge_list):
#       print("half edge id", half_edge.id)
#       if half_edge.next:
#           print("next", half_edge.next.id)
#       else:
#           print("next: None")
#       if half_edge.twin:
#           print("twin", half_edge.twin.id)
#       else:
#           print("twin: None")
#       print("verts", half_edge.edge.vert1, half_edge.edge.vert2)
#       print("\n")

  # delete selected object
  #cmds.delete()
  return half_edge_mesh


def not_seen_face(v1, v2, v3, seen):
   for face in seen:
       if v1 in face and v2 in face and v3 in face:
           return False
   return True

#Convert half-mesh data structure example into Maya mesh
def heMesh_to_maya(heMesh):
  """
  Convert the given half edge mesh to a Maya mesh object
  :param HalfEdgeMesh heMesh: The half edge mesh.
  """
  #List of vertices seen so far in mesh
  vertice_list = []
  #List of vertice ID's
  vertice_ids = []
  #connection data for vertice indices
  polyConnects = []
  #list to help add vertices to list
  verts_temp = []
  #seen_faces
  seen_faces = []
  #starting halfEdge
  start_he = heMesh.halfEdge
  he = heMesh.halfEdge
  face_count = 0
  he_set = {he}
  seen_set = {he.id}
 
  #iterate through all vertices on mesh
  while(True):
      if len(he_set) == 0:
          break
      else:
          he = he_set.pop()
      start_he = he
      #while we haven't seen the original halfEdge, iterate through vertices on this face
      while(True):
           #get all vertice positions of this face
           this_vertex_id = he.vert.id
 
           #if vertex does not exist in vertex list
           if not(this_vertex_id in vertice_ids):
               vertice_list.append(he.vert)
               vertice_ids.append(this_vertex_id)
 
           #index of id in list
           index = vertice_ids.index(this_vertex_id)
 
           verts_temp.append(index)
 
           #add all vertices in this face
           if(len(verts_temp) == 3):
               #ensure this face hasn't been previously added 
               if not_seen_face(verts_temp[0], verts_temp[1], verts_temp[2], seen_faces):
                   polyConnects.append(verts_temp[0])
                   polyConnects.append(verts_temp[1])
                   polyConnects.append(verts_temp[2])
                   seen_faces.append([verts_temp[0], verts_temp[1], verts_temp[2]])
                   face_count += 1
               verts_temp = []
 
           #find other faces to traverse around
           if not he.twin == None:
               if he.twin.id not in seen_set:
                   he_set.add(he.twin)
 
           #go to next half edge on this face
           he = he.next
           seen_set.add(he.id)
             
           #reached start
           if(he.id == start_he.id):
               break
  #maya mesh
  meshFn = OpenMaya.MFnMesh()
  vertices = []
  # list of vertex points
  for vert in vertice_list:
      vertices.append(OpenMaya.MPoint(vert.x, vert.y, vert.z))
  # list of number of vertices per polygon
  # Mesh has face_count # of faces of 3 vertices each
  # hardcoded triangle
  polygonFaces = [3] * face_count

#   print("FACES", face_count)
#   print("vertice_list count", len(vertice_list))
#   print("FINAL EDGE COUNT", len(seen_set) / 2)

  # list of vertex indices that make the
  # the polygons in our mesh
  polygonConnects = polyConnects
  # create the mesh

#   print("vertices", vertices)
#   print("polygonFaces", polygonFaces)
#   print("polygonConnects", polygonConnects)
#   print("len poly connects", len(polygonConnects))

  new_mesh_object = meshFn.create(vertices, polygonFaces, polygonConnects )
  depNode = OpenMaya.MFnDependencyNode(new_mesh_object)
  #Set name of new object
  depNode.setName("Reduced_Object")
  #Get name of new object
  this_name = depNode.name()
  #get currently selected object
  selected = cmds.ls(sl=True,long=True) or []
  sel = cmds.ls(this_name, l=True)
  cmds.sets(sel, e=True, forceElement='initialShadingGroup')
  cmds.select( this_name )
  #fix normals near hard edges
  cmds.polySoftEdge( a=30 )
  #clear selection
  cmds.select(clear=True)
  #hide all objects
  cmds.hide(allObjects=True)
  #unhide latest created mesh so that it's the only one visible
  cmds.showHidden( this_name )
  #Select the original
  cmds.select( selected )

# he_data = maya_to_heMesh()
# this_he = he_data.halfEdge 
# count = 0
# while(True):
#     if not this_he.twin == None:
#         new_he =  this_he
#         break
#     else:
#         this_he = this_he.next
#     if count >=5:
#         new_he = this_he
#         break

#new_he = reduce_he(this_he)
# new_he = reduce_many_he(this_he, 4)
# heMesh_to_maya(new_he)
