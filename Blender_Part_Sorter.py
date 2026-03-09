bl_info = {
    "name": "Blender Part Sorter",
    "author": "RSDT",
    "version": (0, 9),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > NFS Tools",
    "description": "Agrupa objetos en colecciones para mantener orden.",
    "category": "Object",
}

import bpy
from bpy.app.handlers import persistent
from collections import defaultdict
import time
import re

MIN_COUNT = 3
IGNORED_PREFIXES = {"LOD", "HIGH", "LOW", "DAM", "GLASS", "INT", "SHADOW", "BROKEN"}

_last_run = 0.0
_DEBOUNCE = 0.4

def get_prefix(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return ""
    
    match = re.match(r'^([A-Za-z0-9]+)[_.-]?', name)
    if not match:
        return ""
    
    pref = match.group(1).upper()
    if pref.isdigit():
        return ""
    return pref


def prefix_matches_collection_name(prefix: str, coll_name: str) -> bool:
    p = prefix.upper()
    c = coll_name.upper()
    return c.startswith(p) and any(word in c for word in ["PART", "PARTS", "KIT", "PIEZAS"])


def find_or_create_collection(prefix: str) -> bpy.types.Collection | None:
    prefix_upper = prefix.upper()
    scene_coll = bpy.context.scene.collection
    
    for coll in bpy.data.collections:
        if prefix_matches_collection_name(prefix_upper, coll.name):
            return coll
    
    new_name = f"{prefix}_PARTS"
    new_coll = bpy.data.collections.new(new_name)
    scene_coll.children.link(new_coll)
    return new_coll


def is_root_or_system_collection(coll) -> bool:
    if not coll:
        return True
    name_lower = coll.name.lower()
    return (
        name_lower in {"master", "scene collection", "collection"} or
        name_lower.startswith(".") or
        coll == bpy.context.scene.collection
    )


@persistent
def auto_sort_parts(scene, depsgraph):
    global _last_run
    
    now = time.time()
    if now - _last_run < _DEBOUNCE:
        return
    _last_run = now
    
    if getattr(auto_sort_parts, "is_running", False):
        return
    
    auto_sort_parts.is_running = True
    
    try:
        prefix_groups = defaultdict(list)
        
        for obj in bpy.data.objects:
            if obj.type not in {'MESH', 'EMPTY', 'CURVE', 'ARMATURE'}:
                continue
            
            pref = get_prefix(obj.name)
            if not pref or pref in IGNORED_PREFIXES:
                continue
            
            prefix_groups[pref].append(obj)
        
        for pref, objects in prefix_groups.items():
            if len(objects) < MIN_COUNT:
                continue
            
            target_coll = find_or_create_collection(pref)
            if not target_coll:
                continue
            
            for obj in objects:
                for coll in list(obj.users_collection):
                    if coll != target_coll:
                        coll.objects.unlink(obj)
                
                if target_coll not in obj.users_collection:
                    target_coll.objects.link(obj)
    
    except Exception as e:
        print(f"Part Sorter error: {str(e)}")
    
    finally:
        auto_sort_parts.is_running = False


class NFS_PT_PartSorter(bpy.types.Panel):
    bl_label = "Part Sorter (NFS)"
    bl_idname = "NFS_PT_partsorter_v9"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'NFS Tools'
    
    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Auto-activo (≥ {MIN_COUNT} objetos)")
        layout.operator("scene.force_parts_sort", text="Ordenar ahora", icon='FILE_REFRESH')


class NFS_OT_ForceSort(bpy.types.Operator):
    bl_idname = "scene.force_parts_sort"
    bl_label = "Forzar ordenamiento"
    
    def execute(self, context):
        auto_sort_parts(bpy.context.scene, None)
        self.report({'INFO'}, "Ordenamiento manual ejecutado")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(NFS_PT_PartSorter)
    bpy.utils.register_class(NFS_OT_ForceSort)
    bpy.app.handlers.depsgraph_update_post.append(auto_sort_parts)
    auto_sort_parts.is_running = False


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(auto_sort_parts)
    bpy.utils.unregister_class(NFS_OT_ForceSort)
    bpy.utils.unregister_class(NFS_PT_PartSorter)


if __name__ == "__main__":
    register()
