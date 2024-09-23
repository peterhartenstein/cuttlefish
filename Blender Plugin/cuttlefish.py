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
import time as t
import numpy as np
from pathlib import Path
from bpy.props import(StringProperty, PointerProperty, BoolProperty, EnumProperty, IntProperty)
from bpy.types import (Panel, PropertyGroup, Operator)

print("start---------------------------------------------------------------------")

def framessequence_list():

    tool_settings = bpy.context.scene.my_tool

    #option1: use timeline settings
    if tool_settings.frame_selection_mode == 'TIMELINE':
        start = bpy.data.scenes["Scene"].frame_start
        end = bpy.data.scenes["Scene"].frame_end
        frames = list(range(start, end + 1))
    
    #option 2: start, end, step
    elif tool_settings.frame_selection_mode == 'RANGE':
        start = tool_settings.start_frame
        end = tool_settings.end_frame
        step = tool_settings.step_rate
        frames = list(range(start, end + 1, step))
    
    #option 3: custom list
    elif tool_settings.frame_selection_mode == 'CUSTOM':
        input_string = tool_settings.custom_frames_input
        frames = [int(x) for x in input_string.split(',') if x.strip().isdigit()]
    
    return frames

def get_vertco(FRAMES, obj):

    frame_quantity = len(FRAMES)

    #account for dependencies / evaluate obj
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
  
    frame_selection_mode: EnumProperty(
        name="Frame Selection Mode",
        description="Choose how to select frames",
        items=[
            ('TIMELINE', "Use Timeline Settings", "Use frames from Blender's timeline"),
            ('RANGE', "Start, End, Step Rate", "Specify start, end, and step rate"),
            ('CUSTOM', "Custom Frame List", "Enter custom frame numbers")
        ],
        default='TIMELINE'
    )
    
    # start, end, step
    start_frame: IntProperty(
        name="Start Frame",
        description="Start frame",
        default=1
    )
    end_frame: IntProperty(
        name="End Frame",
        description="End frame",
        default=10
    )
    step_rate: IntProperty(
        name="Step Rate",
        description="Step rate for frames",
        default=1
    )

    # csv as string
    custom_frames_input: StringProperty(
        name="Custom Frames",
        description="Enter frames separated by commas, e.g., 1,2,3,10",
        default="1,2,3"
    )

    selected_object: PointerProperty(
        name="Object",
        type = bpy.types.Object,
        description = "Object to export"
    )


class ExportVertCoords(bpy.types.Operator):

    bl_idname = "object.export_vert_coords"
    bl_label = "Export Vert Coords"
    
    @classmethod
    def poll(cls, context):
        return context.scene.my_tool.selected_object is not None

    def execute(self, context):
        start_time = t.time()

        obj = context.scene.my_tool.selected_object
        frames = framessequence_list()
        a = get_vertco(frames, obj)
        
        filepath = context.scene.my_tool.path + "\data.npy"
        save_npy(a,filepath)

        end_time = t.time()
        elapsed_time = end_time - start_time
        VIEW3D_PT_cuttlefish.timer(elapsed_time)
        return {'FINISHED'}


class VIEW3D_PT_cuttlefish(bpy.types.Panel):

    bl_idname = "VIEW3D_PT_cuttlefish"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bl_category = "cuttlefish"
    bl_label = "cuttlefish options"
    elapsed_time = 0
    
    def draw(self, context):
                
        layout = self.layout
        scene = context.scene
        my_tool = scene.my_tool
        
        #object pipette
        row = layout.row()
        row.prop(my_tool, "selected_object", text="Object")

        #object info
        if my_tool.selected_object:
            row = layout.row()
            row.label(text="Selected Object: {}".format(my_tool.selected_object.name))

            row = layout.row()
            row.label(text="Vertex Count: {}".format(len(my_tool.selected_object.data.vertices)))

        #save file path
        row = layout.column(align=True)
        row.prop(scene.my_tool, "path", text ="")

        #Frame Selection Mode
        row = layout.row()
        row.prop(my_tool, "frame_selection_mode", text="Frame Selection Mode")

        #use timeline settings
        if my_tool.frame_selection_mode == 'TIMELINE':
            row = layout.row()
            row.label(text="Using Timeline Settings")

        #start end step
        elif my_tool.frame_selection_mode == 'RANGE':
            row = layout.row()
            row.prop(my_tool, "start_frame", text="Start Frame")
            row = layout.row()
            row.prop(my_tool, "end_frame", text="End Frame")
            row = layout.row()
            row.prop(my_tool, "step_rate", text="Step Rate")

        #custom frame list
        elif my_tool.frame_selection_mode == 'CUSTOM':
            row = layout.row()
            row.prop(my_tool, "custom_frames_input", text="Custom Frames")

        #export button
        row = layout.row()
        row.operator("object.export_vert_coords")             

        #timer result
        row = layout.row()
        row.label(text = "Elapsed Time: {}".format(str(round(self.elapsed_time, 3))))
    
    @staticmethod
    def timer(elapsed_time):
        VIEW3D_PT_cuttlefish.elapsed_time = elapsed_time
            

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
