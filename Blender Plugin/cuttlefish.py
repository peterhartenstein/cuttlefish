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
import os
from pathlib import Path
from bpy.props import(StringProperty, PointerProperty)
from bpy.types import (Panel, PropertyGroup)


def framessequence_list():

    start = bpy.data.scenes["Scene"].frame_start
    end = bpy.data.scenes["Scene"].frame_end

    frames = list(range(start,end+1))
    return frames

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
    
    return vert_data


def save_npy(np_array, filepath):
    
    np.save(filepath, np_array)


class MyProperties(PropertyGroup):

    path: StringProperty(
        name="",
        description="Path to Directory",
        default="",
        maxlen=1024,
        subtype='DIR_PATH') 
  

class ExportVertCoords(bpy.types.Operator):

    bl_idname = "object.export_vert_coords"
    bl_label = "Export Vert Coords"
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):                                  # implement+return timer
        a = get_vertco(framessequence_list())
        filepath = context.scene.my_tool.path + "\data.npy"
        save_npy(a,filepath)
        #print(a)                                                #print
        #print(filepath)                                         #print
        return {'FINISHED'}


class VIEW3D_PT_cuttlefish(bpy.types.Panel):

    bl_idname = "VIEW3D_PT_cuttlefish"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bl_category = "cuttlefish"
    bl_label = "cuttlefish options"
    
    
    def draw(self, context):
                
        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        row.label(text="Active Object: {}".format(context.object.name))

        row = layout.row()
        row.label(text="Vertex Count: {}".format(len(context.object.data.vertices)))

        row = layout.column(align=True)
        row.prop(scene.my_tool, "path", text ="")

        row = layout.row()
        row.operator("object.export_vert_coords")             
      
            

#----------------------------------------------------------------
# Registration

classes = (
    MyProperties,
    ExportVertCoords,
    VIEW3D_PT_cuttlefish
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.mytool
    

if __name__ == "__main__":
    register()
