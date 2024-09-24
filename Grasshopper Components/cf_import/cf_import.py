import Rhino
import numpy as np
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import os
import time as t

"""
component inputs(name - type):
    frame_request - int
    whole_animation - bool
    directory_path - File Path (Folder)
    
component outputs(name - type):
    out - terminal, gh specific
    elapsed_time - str
    mesh_frame - Rhino.Geometry.Mesh
    mesh_frames - List of Rhino.Geometry.Mesh
"""

start_time = t.time()

# Match Blender's timeline indexing
frame_request = frame_request - 1

def load_data(file_path, allow_pickle=False):
    return np.load(file_path, allow_pickle=allow_pickle)

def load_vertices(directory_path):
    vert_file = os.path.join(directory_path, "vertices.npy")
    return load_data(vert_file).astype(np.float64)

def load_edges(directory_path):                                 # not in use, keep for later
    edge_file = os.path.join(directory_path, "edges.npy")
    return load_data(edge_file).astype(np.int32)

def load_faces(directory_path):
    face_file = os.path.join(directory_path, "faces.npy")
    faces = load_data(face_file, allow_pickle=True)
    return faces

def create_mesh(vertices, faces):
    mesh = Rhino.Geometry.Mesh()
    
    #Add vertices to the mesh
    for vert in vertices:
        mesh.Vertices.Add(vert[0], vert[1], vert[2])

    for face in faces:
        if isinstance(face, list) and len(face) >= 3:
            mesh.Faces.AddFace(*face)
    return mesh

def process_frames(directory_path, frame_request, whole_animation):
    vertices = load_vertices(directory_path)
    faces = load_faces(directory_path)

    mesh_frames = DataTree[Rhino.Geometry.Mesh]()

    if whole_animation:
        frames = range(vertices.shape[0])
        for frame in frames:
            mesh = create_mesh(vertices[frame], faces[frame])
            mesh_frames.Add(mesh, GH_Path(frame))
        return create_mesh(vertices[frame_request], faces[frame_request]), mesh_frames 
    else:
        return create_mesh(vertices[frame_request], faces[frame_request]), None

mesh_frame, mesh_frames = process_frames(directory_path, frame_request, whole_animation)

end_time = t.time()
elapsed_time = "{} seconds".format(str(round(end_time - start_time, 3)))