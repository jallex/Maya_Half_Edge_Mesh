
import maya.api.OpenMaya as OpenMaya

#Classes and methods representing the half edge data structure

#Vertex data 
class Vertex:
    def __init__(self, x, y, z, half_edge, id):
        self.x = x
        self.y = y
        self.z = z
        #HalfEdge starting from this Vertex
        self.half_edge = half_edge
        self.id = id

#Face data
class Face:
    def __init__(self, start_edge, id):
        #starting half-edge
        self.start_edge = start_edge
        self.id = id

#HalfEdge data
class HalfEdge:
    def __init__(self):
        pass
    
    #set half edge data
    def set(self, face, vert, next, twin, id):
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

#HalfEdge Mesh data
class HalfEdgeMesh:
    def __init__(self, halfEdge):
        self.halfEdge = halfEdge


#Create some example data
#HalfEdges example data
half_edge_example1 = HalfEdge()
he1_twin = HalfEdge()
he1_next = HalfEdge()
half_edge_example2 = HalfEdge()
he2_twin = HalfEdge()
he2_next = HalfEdge()
half_edge_example3 = HalfEdge()
he3_twin = HalfEdge()
he3_next = HalfEdge()
half_edge_example4 = HalfEdge()
he4_twin = HalfEdge()
he4_next = HalfEdge()

#Vertice example data
v1 = Vertex(-0.500000, -0.500000, 0.500000, he1_twin, 1)
v2 = Vertex(-0.500000, -0.500000, -0.500000, he2_twin, 2)
v3 = Vertex(0.500000, -0.500000, -0.500000, he3_twin, 3)
v4 = Vertex(0.500000, -0.500000, 0.500000, he4_twin, 4)
v5 = Vertex(0.000000, -0.500000, 0.000000, half_edge_example1, 5)

#Face example data
f1 = Face(half_edge_example1, 1)
f2 = Face(half_edge_example2, 2)
f3 = Face(half_edge_example3, 3)
f4 = Face(half_edge_example4, 4)

#HalfEdge example data continued
half_edge_example1.set(f1, v1, he1_next, he1_twin, 1)
he1_twin.set(f4, v5, half_edge_example4, half_edge_example1, 5)
he1_next.set(f1, v2, he2_twin, None, 6)
half_edge_example2.set(f2, v2, he2_next, he2_twin, 2)
he2_twin.set(f1, v5, half_edge_example1, half_edge_example2, 7)
he2_next.set(f2, v3, he3_twin, None, 8)
half_edge_example3.set(f3, v3, he3_next, he3_twin, 3)
he3_twin.set(f2, v5, half_edge_example2, half_edge_example3, 9)
he3_next.set(f3, v4, he4_twin, None, 10)
half_edge_example4.set(f4, v4, he4_next, he4_twin, 4)
he4_twin.set(f3, v5, half_edge_example3, half_edge_example4, 11)
he4_next.set(f4, v1, he1_twin, None, 12)

#HalfEdge Mesh example data
heMesh = HalfEdgeMesh(he2_twin)

#Convert half-mesh data structure example into Maya mesh
def heMesh_to_maya(heMesh):
    """
    Convert the given half edge mesh to a Maya mesh object 

    :param HalfEdgeMesh heMesh: The half edge mesh.
    """
    #List of vertices in mesh
    vertice_list = []
    #List of vertice ID's 
    vertice_ids = []
    #connection data for vertice indices
    polyConnects = []
    #list to help add vertices to list
    verts_temp = []

    #starting halfEdge
    start_he = heMesh.halfEdge
    he = heMesh.halfEdge
    #While we haven't seen the original halfEdge, iterate through each face
    while(True):
        he_temp = he
        start_he2 = he
        #while we haven't seen the original halfEdge, iterate through  vertices on this face
        while(True):
            #get all vertice positions of this face
            this_vertex_id = he_temp.vert.id
            #if vertex does not exist in vertex list
            if not(this_vertex_id in vertice_ids):
                vertice_list.append(he_temp.vert)
                vertice_ids.append(this_vertex_id)
            #index of id in list
            index = vertice_ids.index(this_vertex_id)

            verts_temp.append(index)
            #add all vertices in this face
            if(len(verts_temp) == 3):
                polyConnects.append(verts_temp[0])
                polyConnects.append(verts_temp[1])
                polyConnects.append(verts_temp[2])
                verts_temp = []

            #go to next half edge on this face
            he_temp = he_temp.next
            if(he_temp.id == start_he2.id):
                break

        #go to next face
        he = he.next.twin
        if(he.id == start_he.id):
            break

    #maya mesh 
    meshFn = OpenMaya.MFnMesh()

    vertices = []
    # list of vertex points
    for vert in vertice_list:
        vertices.append(OpenMaya.MPoint(vert.x, vert.y, vert.z))

    # list of number of vertices per polygon
    # Mesh has 4 faces of 3 vertices each
    polygonFaces = [3] * 4

    # list of vertex indices that make the 
    # the polygons in our mesh
    polygonConnects = polyConnects

    print("vertices list ", vertices)
    print("polygonConnects list ", polygonConnects)

    # create the mesh
    meshFn.create(vertices, polygonFaces, polygonConnects )

def maya_to_heMesh():
    """

    Convert the selected object in Maya to a half edge mesh.
    
    :returns: :class:'HalfEdgeMesh' the selected object as a half edge mesh data structure.
    """
    #get first selected object
    selected_object = OpenMaya.MGlobal.getActiveSelectionList(0)
    dag = selected_object.getDagPath(0)
    print(dag)
    mesh = OpenMaya.MFnMesh(dag)
    print(mesh)
    poly = OpenMaya.MItMeshPolygon(dag)
    print(poly)
    visited = set([0])

    half_edge1 = HalfEdge()

    while not poly.isDone():
        # examples of selecting verts/edges/faces by index from object

        #cmds.select( str(selected_object)[2:-2] + '.vtx[' + str(0) + ']' )
        #cmds.select( str(selected_object)[2:-2] + '.e[' + str(0) + ']' )
        #cmds.select( str(selected_object)[2:-2] + '.f[' + str(0) + ']' )
        current = poly.index()
        vertices = mesh.getPolygonVertices(current)
        connected_faces = poly.getConnectedFaces()
        for face in connected_faces:
            if (face in visited):
                continue
            visited.add(face)
            print("face", face)
            face_verts = mesh.getPolygonVertices(face)
            vert_count = len(face_verts)
            for vert in range(vert_count):
                print("vert", vert)
        poly.next()
                       
#heMesh_to_maya(heMesh)
maya_to_heMesh()
