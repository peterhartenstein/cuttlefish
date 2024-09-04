import Rhino
import numpy as np
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import time as t

"""
component inputs(name - type):
    frame_request - int
    whole_animation - bool
    file_path - File Path
    

component outputs(name - type):
    out - terminal, gh specific
    elapsed_time - str
    frames - ghdoc Object
    frame - ghdoc Object
"""

start_time = t.time()

# Match Blender's timeline indexing
frame_request = frame_request - 1

def load_vert_data(file_path):

    return np.load(file_path, mmap_mode="r").astype(np.float64)

def create_point_tree(vert_data, frames):

    tree = DataTree[object]()
    vertcount = vert_data.shape[1]
    
    for frame in frames:
        frame_path = GH_Path(frame)
        points = [Rhino.Geometry.Point3d(vert_data[frame, vert, 0],  # x
                                         vert_data[frame, vert, 1],  # y
                                         vert_data[frame, vert, 2])  # z
                  for vert in range(vertcount)]
        for point in points:
            tree.Add(point, frame_path)

    return tree

def process_frames(file_path, frame_request, whole_animation):

    vert_data = load_vert_data(file_path)
    
    if whole_animation:
        frames = range(vert_data.shape[0])
        tree_all_frames = create_point_tree(vert_data, frames)
        tree_frame = create_point_tree(vert_data, [frame_request])
        return tree_all_frames, tree_frame

    else:
        frames = [frame_request]
        tree_frame = create_point_tree(vert_data, frames)
        return None, tree_frame


frames, frame = process_frames(file_path, frame_request, whole_animation)

end_time = t.time()
elapsed_time = "{} seconds".format(str(round(end_time - start_time, 3)))