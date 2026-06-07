import bpy
import random
import os
import math
from mathutils import Vector

def move_local(obj, x=0.0, y=0.0, z=0.0):
    delta = Vector((x, y, z))
    obj.location += obj.matrix_world.to_quaternion() @ delta

def get_original_settings() -> dict[str:dict]:
    og = dict()
    cameras = bpy.data.collections.get("Cameras")
    
    for cam in cameras.objects:
        temp = dict()
        temp["loc"] = cam.location.xyz.copy()
        temp["rot"] = cam.rotation_euler.copy()
        og[cam.name] = temp
    
    return og

def move_cameras(translation: bool,
                 rotation: bool,
                 translation_y_range: float = 0.6,
                 translation_z_range: float = 0.2,
                 rotation_range: float = 5.):

    cameras = bpy.data.collections.get("Cameras")

    for cam in cameras.objects:
        if translation:
            dy = random.uniform(-translation_y_range, translation_y_range)
            dz = random.uniform(-translation_z_range, translation_z_range)
            
            move_local(cam, 0, dy, dz)

        if rotation:
            base_rot = cam.rotation_euler.copy()
            cam.rotation_euler = (
                base_rot.x,
                base_rot.y,
                base_rot.z  + math.radians(random.uniform(-rotation_range, rotation_range))
            )
        
def reset_cameras(original_settings: dict):
    cameras = bpy.data.collections.get("Cameras")
    
    for cam in cameras.objects:
        data = original_settings[cam.name]
        cam.location = data["loc"]
        cam.rotation_euler = data["rot"]
