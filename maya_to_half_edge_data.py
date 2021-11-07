from typing import Counter
import maya.api.OpenMaya as OpenMaya

#Classes and methods representing the half edge data structure

#Vertex data 
class Vertex:
    def __init__(self, x, y, z):
        self.x = None
        self.y = None
        self.z = None

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

#add the edges on this face to the face object
def get_edges_on_faces(faces, edges):
    for f in faces:
        verts = f.verts
        for e in edges:
            if e.vert1 in verts and e.vert2 in verts:
                f.edges.append(e)
    return faces

def maya_to_heMesh():
    """

    Convert the selected object in Maya to a half edge mesh.
    
    :returns: :class:'HalfEdgeMesh' the selected object as a half edge mesh data structure.
    """
    #get first selected object
    selected_object = OpenMaya.MGlobal.getActiveSelectionList(0)
    dag = selected_object.getDagPath(0)
    poly = OpenMaya.MItMeshPolygon(dag)

    edge_list = []
    face_list = []
    half_edge_list = []

    edges_verts = []
    #Iterate through each face of the poly
    while not poly.isDone():
        face = poly.index()
        #get verts on face in winding order
        face_verts = poly.getVertices()

        vert_iter = iter(face_verts)
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

    print(edges_verts)

    face_num = 0
    edge_count = 0
    #Create edges and half-edges
    for index, edge in enumerate(edges_verts):
        #vertices are in order that the half-edge should be facing
        this_edge = Edge(edge[0], edge[1], index)
        #find if pre-existing edge exists
        for e in edge_list:
            if (e.vert1 == edge[0] and e.vert2 == edge[1]) or (e.vert1 == edge[1] and e.vert2 == edge[0]):
                this_edge = e
                print("this edge is shared:", e.id, "verts:", e.vert1,e.vert2, "edge:", edge, )
        edge_list.append(this_edge)
        edges_on_this_face.append(this_edge)

        #Create half-edge
        half_edge = HalfEdge()
        half_edge.edge = this_edge
        half_edge.face = face

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
        
        print(edge_count)
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

    print("HALF EDGE DATA")
    for index, half_edge in enumerate(half_edge_list):
        print("half edge id", half_edge.id)
        if half_edge.next:
            print("next", half_edge.next.id)
        else:
            print("next: None")
        if half_edge.twin:
            print("twin", half_edge.twin.id)
        else:
            print("twin: None")
        print("verts", half_edge.edge.vert1, half_edge.edge.vert2)

        print("\n")

    return half_edge_mesh 

maya_to_heMesh()
