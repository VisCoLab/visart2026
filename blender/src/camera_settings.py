import bpy
import random
import os


def get_original_settings() -> dict[str:dict]:
    og = dict()
    cameras = bpy.data.collections.get("Cameras")
    
    for cam in cameras.objects:
        temp = dict()
        temp["loc"] = cam.location.xyz.copy()
        temp["rot"] = cam.rotation_euler.copy()
        og[cam.name] = temp
    
    return og

def move_cameras(translation_strength: float = 0.2,
                 rotation_speed: float = 0.1):
    cameras = bpy.data.collections.get("Cameras")
    
    for cam in cameras.objects:
        base_loc = cam.location.copy()
        base_rot = cam.rotation_euler.copy()
        s = random.choice([-1, 1])
        
        dx = s*(random.random() * 3.0) * translation_strength
        dy = s*(random.random() * 3.0) * translation_strength
        dz = s*(random.random() * 3.0) * translation_strength * 0.5
        
        cam.location = (
            base_loc.x + dx,
            base_loc.y + dy,
            base_loc.z + dz
        )
        cam.rotation_euler = (
            base_rot.x,
            base_rot.y,
            base_rot.z  + s*random.random()*rotation_speed
        )
        
def reset_cameras(original_settings: dict):
    cameras = bpy.data.collections.get("Cameras")
    
    for cam in cameras.objects:
        data = original_settings[cam.name]
        cam.location = data["loc"]
        cam.rotation_euler = data["rot"]

if __name__=="__main__":
    og = get_original_settings()
    move_cameras()
    sleep(5)
    reset_cameras(og)