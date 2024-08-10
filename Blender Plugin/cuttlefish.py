bl_info = {
    "name": "cuttlefish",
    "author": "Peter Hartenstein",
    "version": (0, 0, 1),
    "blender": (4, 20, 0),
    "location": "3D Viewport > Sidebar > cuttlefish",
    "description": "Translating animated geometry from Blender to Grasshopper",
    "category": "Export",
    }


import bpy
import numpy as np
import time as t
from os import system


def framessequence_list():

    start = bpy.data.scenes["Scene"].frame_start
    end = bpy.data.scenes["Scene"].frame_end

    frames = list(range(start,end))
    

def get_vertco(FRAMES):

    frame_quantity = len(FRAMES)

    #account for dependencies / evaluate obj
    obj = bpy.context.object
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    #amount of verts in mesh
    verts = obj_eval.data.vertices
    vertcount = len(verts)

    #create matrix / x=frames, y=verts, z=xyz
    vert_data = np.empty(shape=(frame_quantity, vertcount, 3), dtype=np.float16)

    #cycle through FRAMES
    for i in range(frame_quantity):

        #jump to frame
        bpy.context.scene.frame_set(FRAMES[i])

        #account for dependencies / evaluate obj
        obj = bpy.context.object
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        
        verts = obj_eval.data.vertices 
      
        #allocate vector to matrix
        for j in range(vertcount):
            
            vertco = obj.matrix_world @ verts[j].co 
            vert_data[i, j, 0] = vertco[0]
            vert_data[i, j, 1] = vertco[1]
            vert_data[i, j, 2] = vertco[2]
    
    return vert_data, vertcount


def save_npy(np_array):
    np.save("npy_data/data.npy", np_array)




class VIEW3D_PT_cuttlefish(bpy.types.Panel):

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bl_category = "cuttlefish"
    bl_label = "cuttlefish options"
    
    
    def draw(self, context):
        row = self.layout.row()
        row.operator("Save Location", text="file path")
            




def register():
    bpy.utils.register_class(VIEW3D_PT_cuttlefish)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_cuttlefish)
    

if __name__ == "__main__":
    register()
