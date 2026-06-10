import bpy
import random
import os
import math
from mathutils import Vector

def move_local(obj, x=0.0, y=0.0, z=0.0):
    delta = Vector((x, y, z))
    obj.location += obj.matrix_world.to_quaternion() @ delta

def get_original_settings(cams: list[object]) -> dict[str:dict]:
    og = dict()
    
    for cam in cams:
        temp = dict()
        temp["loc"] = cam.location.xyz.copy()
        temp["rot"] = cam.rotation_euler.copy()
        og[cam.name] = temp
    
    return og

def move_cameras(cams: list[object],
                 translation: bool,
                 rotation: bool,
                 translation_y_range: float = 0.5,
                 translation_z_range: float = 1.,
                 rotation_range: float = 5.):

    for cam in cams:
        if translation:
            base_loc = cam.location.copy()
            dy = random.uniform(-translation_y_range, translation_y_range)
            dz = random.uniform(-translation_z_range, translation_z_range)
            
            cam.location = (
                base_loc.x,
                base_loc.y + dy,
                base_loc.z + dz,
            )
        
        if rotation:
            base_rot = cam.rotation_euler.copy()
            cam.rotation_euler = (
                base_rot.x,
                base_rot.y,
                base_rot.z  + math.radians(random.uniform(-rotation_range, rotation_range))
            )
        
def reset_cameras(cams: list[object],
                  original_settings: dict):
    for cam in cams:
        data = original_settings[cam.name]
        cam.location = data["loc"]
        cam.rotation_euler = data["rot"]
