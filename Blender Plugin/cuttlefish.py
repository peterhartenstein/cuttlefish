bl_info = {
    "name": "cuttlefish",
    "author": "Peter Hartenstein",
    "version": (0, 0, 4),
    "blender": (4, 20, 0),
    "location": "3D Viewport > Sidebar > cuttlefish",
    "description": "Translating animated geometry from Blender to Grasshopper",
    "category": "Export",
    }


import bpy
import time as t
import numpy as np
import csv
import json
from pathlib import Path
from bpy.props import(StringProperty, PointerProperty, BoolProperty, EnumProperty, IntProperty)
from bpy.types import (Panel, PropertyGroup, Operator)

print("start---------------------------------------------------------------------")

def framessequence_list():

    tool_settings = bpy.context.scene.cuttlefish_tool

    #option 1: use timeline settings
    if tool_settings.frame_selection_mode == 'TIMELINE':
        start = bpy.data.scenes["Scene"].frame_start
        end = bpy.data.scenes["Scene"].frame_end
        frames = list(range(start, end + 1))

    #option 2: current frame
    elif tool_settings.frame_selection_mode == 'CURRENT':
        current_frame = bpy.context.scene.frame_current
        frames = [current_frame]
    
    #option 3: start, end, step
    elif tool_settings.frame_selection_mode == 'RANGE':
        start = tool_settings.start_frame
        end = tool_settings.end_frame
        step = tool_settings.step_rate
        frames = list(range(start, end + 1, step))
    
    #option 4: custom list
    elif tool_settings.frame_selection_mode == 'CUSTOM':
        input_string = tool_settings.custom_frames_input
        frames = [int(x) for x in input_string.split(',') if x.strip().isdigit()]
    
    #option 5: csv file
    elif tool_settings.frame_selection_mode == 'CSV':
        frames = []
        try:
            with open(tool_settings.csv_file_path, mode='r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    for value in row:
                        try:
                            frames.append(int(value))
                        except ValueError:
                            raise ValueError(f"Error: '{value}' in CSV is not an integer")
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: File '{tool_settings.csv_file_path}' not found")

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


def get_edges(FRAMES, obj, calculate_per_frame):
    
    frame_quantity = len(FRAMES)
    edgecount = len(obj.data.edges)
    
    if calculate_per_frame == "PER_FRAME":
        edge_data = np.empty(shape=(frame_quantity, edgecount, 2), dtype=np.int32)
    else:
        edge_data = np.empty(shape=(edgecount, 2), dtype=np.int32)
        frame_quantity = 1

    for i in range(frame_quantity):
        if calculate_per_frame == "PER_FRAME":
            bpy.context.scene.frame_set(FRAMES[i])

        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        edges = obj_eval.data.edges

        for j, edge in enumerate(edges):
            if calculate_per_frame == "PER_FRAME":
                edge_data[i, j, 0] = edge.vertices[0]
                edge_data[i, j, 1] = edge.vertices[1]
            else:
                edge_data[j, 0] = edge.vertices[0]
                edge_data[j, 1] = edge.vertices[1]
                
    return edge_data


def get_faces(FRAMES, obj, calculate_per_frame):

    framequantity = len(FRAMES)
    facecount = len(obj.data.polygons)

    if calculate_per_frame == "PER_FRAME": 
        face_data = np.empty(shape=(framequantity, facecount), dtype=object)
    else:
        face_data = np.empty(shape=(facecount), dtype=object)  
        framequantity = 1

    for i in range(framequantity):
        if calculate_per_frame == "PER_FRAME":
            bpy.context.scene.frame_set(FRAMES[i])

        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        faces = obj_eval.data.polygons

        for j, face in enumerate(faces):
            if calculate_per_frame == "PER_FRAME":
                face_data[i, j] = [v for v in face.vertices]
            else:
                face_data[j] = [v for v in face.vertices]

    return face_data


def save_npy(np_array, filepath):
    np.save(filepath, np_array)


def save_metadata(base_path, obj_name, edge_face_data, frames, vertex_count, edge_count, face_count):
    metadata = {
        "mesh_name": obj_name,
        "edge_face_data": edge_face_data,
        "frames": frames,
        "vertex_count": vertex_count,
        "edge_count": edge_count,
        "face_count": face_count,
        "export_time": t.strftime("%Y-%m-%d_%H:%M:%S", t.localtime())
    }

    filepath = f"{base_path}/{obj_name}_metadata.json"
    with open(filepath, 'w') as file:
        json.dump(metadata, file, indent=4)


class CuttlefishProperties(PropertyGroup):

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
            ("CURRENT", "Current Frame", "Use the current frame"),
            ('RANGE', "Start, End, Step Rate", "Specify start, end, and step rate"),
            ('CUSTOM', "Custom Frame List", "Enter custom frame numbers"),
            ("CSV", "Frames from CSV", "Select a CSV file with frame numbers")
        ],
        default='TIMELINE'
    )
    
    csv_file_path: StringProperty(
        name="CSV File Path",
        description="Select a CSV file with frame numbers",
        default="File Path",
        maxlen=1024,
        subtype='FILE_PATH'
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

    export_vertices: BoolProperty(
        name="Vertices",
        description="Export vertex data",
        default=True
    )
    export_edges: BoolProperty(
        name="Edges",
        description="Export edge data",
        default=False
    )
    export_faces: BoolProperty(
        name="Faces",
        description="Export face data",
        default=True
    )

    calculate_per_frame: EnumProperty(
        name="Calculate per Frame",
        description="Calculate edge and face data...",
                items=[
            ("PER_FRAME", "calculate for every frame - SLOW", "Calculate edge and face data for every frame"),
            ("ONCE", "calculate once - FAST (default)", "Calculate edge and face data only once")
        ],
        default='ONCE'
    )


class ExportMeshData(bpy.types.Operator):

    bl_idname = "object.export_vert_coords"
    bl_label = "Export Vert Coords"
    
    @classmethod
    def poll(cls, context):
        return context.scene.cuttlefish_tool.selected_object is not None

    def execute(self, context):
        start_time = t.time()
        obj = context.scene.cuttlefish_tool.selected_object
        frames = framessequence_list()
        calculate_per_frame = context.scene.cuttlefish_tool.calculate_per_frame

        base_path = context.scene.cuttlefish_tool.path.replace("\\", "/").rstrip("/")
        obj_name = obj.name.replace(" ", "_")
        edge_face_data = calculate_per_frame # for metadata

        vertex_count = len(obj.data.vertices)
        edge_count = len(obj.data.edges)
        face_count = len(obj.data.polygons)

        save_metadata(base_path, obj_name, edge_face_data, frames, vertex_count, edge_count, face_count)

        if context.scene.cuttlefish_tool.export_vertices:
            vertices = get_vertco(frames, obj)      
            filepath = f"{base_path}/{obj_name}_vertices.npy"
            save_npy(vertices,filepath)

        if context.scene.cuttlefish_tool.export_edges:
            edges = get_edges(frames, obj, calculate_per_frame)
            filepath = f"{base_path}/{obj_name}_edges.npy"
            save_npy(edges,filepath)

        if context.scene.cuttlefish_tool.export_faces:
            faces = get_faces(frames, obj, calculate_per_frame)
            filepath = f"{base_path}/{obj_name}_faces.npy"
            save_npy(faces,filepath)

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
        cuttlefish_tool = scene.cuttlefish_tool
        
        #object pipette
        row = layout.row()
        row.prop(cuttlefish_tool, "selected_object", text="Object")

        #object info
        if cuttlefish_tool.selected_object:
            row = layout.row()
            row.label(text="Selected Object: {}".format(cuttlefish_tool.selected_object.name))

            row = layout.row()
            row.label(text="Vertex Count: {}".format(len(cuttlefish_tool.selected_object.data.vertices)))

        #save file path
        row = layout.column(align=True)
        row.prop(scene.cuttlefish_tool, "path", text ="")


        #Frame Selection Mode
        row = layout.row()
        row.prop(cuttlefish_tool, "frame_selection_mode", text="Frame Selection Mode")

        #use timeline settings
        if cuttlefish_tool.frame_selection_mode == 'TIMELINE':
            row = layout.row()
            row.label(text="Using Timeline Settings")

        #start end step
        elif cuttlefish_tool.frame_selection_mode == 'RANGE':
            row = layout.row()
            row.prop(cuttlefish_tool, "start_frame", text="Start Frame")
            row = layout.row()
            row.prop(cuttlefish_tool, "end_frame", text="End Frame")
            row = layout.row()
            row.prop(cuttlefish_tool, "step_rate", text="Step Rate")

        #custom frame list
        elif cuttlefish_tool.frame_selection_mode == 'CUSTOM':
            row = layout.row()
            row.prop(cuttlefish_tool, "custom_frames_input", text="Custom Frames")

        #csv file
        elif cuttlefish_tool.frame_selection_mode == 'CSV':
            row = layout.row()
            row.prop(cuttlefish_tool, "csv_file_path", text="CSV File")

        #BTogs for vert,edge,face
        row = layout.row()
        row.label(text="Export Mesh Data")
        row = layout.row(align=True)
        row.prop(cuttlefish_tool, "export_vertices", text="Vertices")
        row.prop(cuttlefish_tool, "export_faces", text="Faces")
        row.prop(cuttlefish_tool, "export_edges", text="Edges")
        
        #face and edge calculation
        row = layout.row()
        row.prop(cuttlefish_tool, "calculate_per_frame", text="Face and Edge Data")

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
    CuttlefishProperties,
    ExportMeshData,
    VIEW3D_PT_cuttlefish
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.cuttlefish_tool = PointerProperty(type=CuttlefishProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.cuttlefish_tool
    

if __name__ == "__main__":
    register()
