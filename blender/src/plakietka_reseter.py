import bpy
import random

def reset_plakietka(canvas: str, plakietka: str, margin: float):
    canv = bpy.data.objects[canvas]
    plak = bpy.data.objects[plakietka]
    
    s_x = random.choice([-1,1])
    plak.location.x = s_x*canv.scale.x * margin * 2
    s_z = random.choice([-.7,0,.7])
    plak.location.z = s_z
        