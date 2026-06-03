import bpy
import random
import math

def mod_lights(shape: str, spread: int):
    spread = math.radians(spread)
    lights = bpy.data.objects["light"]
    lights.data.shape = shape
    lights.data.spread = spread

if __name__=="__main__":    
    light_shapes = ["SQUARE", "DISK"]
    shape = random.choice(light_shapes)
    spread = math.radians(random.choice([_ for _ in range(60,180)]))
    mod_lights(shape, spread)