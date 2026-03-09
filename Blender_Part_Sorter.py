bl_info = {
    "name": "Blender Part Sorter",
    "author": "RSDT",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "category": "Object",
    "description": "Esta herramienta crea colecciones segun el tipo de prefijo de los objetos.",
}

import bpy
from collections import defaultdict

MIN_OBJECTS = 3


def get_prefix(name):
    if "_" in name:
        return name.split("_")[0]
    return None


def detect_user_removal(scene):

    for obj in scene.objects:

        if obj.get("ps_autosorted"):

            prefix = get_prefix(obj.name)

            if not prefix:
                continue

            col_name = f"{prefix} Parts"

            if col_name in bpy.data.collections:

                col = bpy.data.collections[col_name]

                if obj.name not in col.objects:
                    obj["ps_user_removed"] = True


def auto_sort(scene):

    prefix_map = defaultdict(list)

    for obj in scene.objects:

        if obj.get("ps_user_removed"):
            continue

        prefix = get_prefix(obj.name)

        if prefix:
            prefix_map[prefix].append(obj)

    for prefix, objs in prefix_map.items():

        if len(objs) < MIN_OBJECTS:
            continue

        col_name = f"{prefix} Parts"

        if col_name not in bpy.data.collections:

            col = bpy.data.collections.new(col_name)
            scene.collection.children.link(col)

        else:
            col = bpy.data.collections[col_name]

        for obj in objs:

            if obj.name not in col.objects:

                col.objects.link(obj)

                obj["ps_autosorted"] = True

                for c in obj.users_collection:
                    if c != col:
                        c.objects.unlink(obj)


def depsgraph_handler(scene, depsgraph):

    detect_user_removal(scene)
    auto_sort(scene)


def register():

    if depsgraph_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_handler)


def unregister():

    if depsgraph_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler)


if __name__ == "__main__":
    register()