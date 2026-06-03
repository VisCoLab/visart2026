import bpy
import random

def reset_floor(floor_name: str):
    prefix = "floor_"

    materials = [
        mat for mat in bpy.data.materials
        if mat.name.startswith(prefix)
    ]

    if materials:
        mat = random.choice(materials)

        obj = bpy.data.objects[floor_name]
        obj.data.materials.clear()
        obj.data.materials.append(mat)

if __name__=="__main__":
    floor_name = "Ground"
    reset_floor(floor_name)