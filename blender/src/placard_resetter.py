import bpy
import random

def reset_placard(canvas_name: str, placard_name: str, margin: float):
    canvas = bpy.data.objects[canvas_name]
    placard = bpy.data.objects[placard_name]

    s_x = random.choice([-1, 1])
    placard.location.x = s_x * canvas.scale.x * margin * 2
    s_z = random.choice([-.7, 0, .7])
    placard.location.z = s_z
