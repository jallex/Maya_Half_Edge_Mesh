# Maya_Half_Edge_Mesh
An implementation of the half edge mesh data structure in Maya using maya.api.OpenMaya (Python API 2.0). 

Behind the scenes, Maya uses the half edge mesh data structure for heavy computations such as decimation. This is a working example of half-edge meshes in Maya and a research project to explore new progressive mesh methods and algorithms, comparing these new methods with Maya's existing algorithms. 

 <p align="left">
   <img src="./demo_images/PM_demo.gif">
  </p>


# How to Use
1. Download the source code, and add to your Maya scripts folder, or edit execute.py to contain the folder to the source code
2. Run execute.py in Maya
3. Select a Mesh object to convert to half edge mesh and click the 'select' button
4. Use the slider to create progressive meshes with user-specified number of faces
