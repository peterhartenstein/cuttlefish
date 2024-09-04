import Rhino
import numpy as np
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import time as t

"""
component inputs(name - type):
    frame_request - int
    file_path - File Path

component outputs(name - type):
    out - terminal, gh specific
    elapsed_time - str
    frames - ghdoc Object
    frame - ghdoc Object
"""

frame_request = frame_request - 1   #match Blenders timeline indexing

start_time = t.time()

vert_data = np.load(file_path, mmap_mode="r", )

frame_quantity = vert_data.shape[0]
vertcount = vert_data.shape[1]      

vert_data = vert_data.astype(np.float64)

tree_allFrames = DataTree[object]()
tree_frame = DataTree[object]()

#reconstruct animation to tree
for frame in range (frame_quantity):
    frame_path = GH_Path(frame)

    for vert in range(vertcount):
        point = Rhino.Geometry.Point3d(vert_data[frame, vert, 0], # x
                                       vert_data[frame, vert, 1], # y
                                       vert_data[frame, vert, 2]) # z
        tree_allFrames.Add(point, frame_path)

        if frame == frame_request:
            tree_frame.Add(point)

end_time = t.time()
elapsed_time = end_time - start_time

#gh component output 
frames = tree_allFrames
frame = tree_frame
elapsed_time = "{} seconds".format(str(round(elapsed_time,3)))