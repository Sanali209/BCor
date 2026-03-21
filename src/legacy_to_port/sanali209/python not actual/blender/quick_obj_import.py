# scripth for importing obj files into blender

import bpy
import os


def finde_object_file(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".obj"):
            return file


def finde_engine_texture(folder_path):
    sufixes = ["thruster_difx.dds", "engine_difx.dds"]
    for file in os.listdir(folder_path):
        file_name = file.lower()
        for suf in sufixes:
            if file_name.endswith(suf):
                return file


def chech_file_by_sufix(file_name, sufixes):
    for suf in sufixes:
        if file_name.endswith(suf):
            return True
    return False


def find_main_texture(folder_path):
    exclude_suf = ["thruster_diff.dds", "engine_diff.dds"]
    include_suf = ["_diff.dds"]
    for file in os.listdir(folder_path):
        file_name = file.lower()
        if file_name.endswith(".dds"):
            exlude = chech_file_by_sufix(file_name, exclude_suf)
            if not exlude:
                include = chech_file_by_sufix(file_name, include_suf)
                if include:
                    return file


# function import object and return object
def ImportObject(folder_path, object_file):
    # import object
    bpy.ops.import_scene.obj(filepath=os.path.join(folder_path, object_file))
    # get object
    imported_object = bpy.context.selected_objects[0]
    # set object to origin
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    # return object
    return imported_object


# function to get all materials from object
def get_materials_from_object(object):
    materials = []
    for slot in object.material_slots:
        materials.append(slot.material)
    return materials


def set_bsdf_node_color_by_texture(material, bsdf_node, texture_path):
    image_texture_node = material.node_tree.nodes.new('ShaderNodeTexImage')
    image_texture_node.image = bpy.data.images.load(texture_path)
    # Link the nodes
    links = material.node_tree.links
    link = links.new(image_texture_node.outputs["Color"], bsdf_node.inputs["Base Color"])


def mathSet(materials):
    for math in materials:
        math_name: str = math.name
        math_name = math_name.lower()
        principled_bsdf = math.node_tree.nodes["Principled BSDF"]
        texture_path = os.path.join(folder_path, find_main_texture(folder_path))
        if 'engine' in math_name:
            # set material
            texture_path = os.path.join(folder_path, finde_engine_texture(folder_path))
        # set texture
        set_bsdf_node_color_by_texture(math, principled_bsdf, texture_path)


folder_path = ""

from bpy.props import StringProperty


class SimplePanel(bpy.types.Panel):
    bl_label = "Custom Panel"
    bl_idname = "PT_CustomPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    folder_path: StringProperty(
        name="Folder Path",
        default="",
        subtype='DIR_PATH'
    )

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "folder_path")
        layout.operator("custom.execute_operator")


class CustomExecuteOperator(bpy.types.Operator):
    bl_label = "Execute"
    bl_idname = "custom.execute_operator"

    def execute(self, context):
        global folder_path
        folder_path = context.scene.folder_path
        self.report({'INFO'}, f"Folder Path: {folder_path}")
        # Add your logic here for what to do with the folder path
        object_file = finde_object_file(folder_path)
        imported_object = ImportObject(folder_path, object_file)
        materials = get_materials_from_object(imported_object)
        mathSet(materials)
        return {'FINISHED'}


classes = (SimplePanel, CustomExecuteOperator)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.folder_path = bpy.props.StringProperty()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.folder_path


if __name__ == "__main__":
    register()
