import bpy
import random
import sys
sys.path.append("/home/neerka/blender/projects/visart26/assets/scripts")
from plakietka_reseter import reset_plakietka

def load_picture(canvas_name: str, 
                 frame_name: str,
                 glass_name: str,
                 desc_name: str, 
                 image_path: str,
                 margin: float):
    # ===== POBRANIE OBIEKTU =====

    obj = bpy.data.objects[canvas_name]
    frame = bpy.data.objects[frame_name]
    glass = bpy.data.objects[glass_name]
    plakietka = bpy.data.objects[desc_name]

    # ===== WCZYTANIE OBRAZU =====

    image = bpy.data.images.load(image_path, check_existing=True)

    # ===== SKALOWANIE CANVASA =====

    w = image.size[0]
    h = image.size[1]
    scale = .7

    aspect = w / h

    if aspect >= 1:
        obj.scale.x = aspect * scale
        obj.scale.y = 1 * scale
    else:
        obj.scale.x = 1 * scale
        obj.scale.y = 1 / aspect * scale

    frame.scale.x = obj.scale.x * margin
    frame.scale.y = obj.scale.y * margin
    
    glass.scale.x = obj.scale.x * margin
    glass.scale.z = obj.scale.y * margin
    
    reset_plakietka(canvas_name, desc_name, margin)

    # ===== MATERIAŁ =====

    mat = obj.active_material

    if mat is None:
        mat = bpy.data.materials.new("CanvasMaterial")
        mat.use_nodes = True
        obj.active_material = mat

    mat.use_nodes = True

    nodes = mat.node_tree.nodes

    # znajdź Principled BSDF
    bsdf = nodes.get("Principled BSDF")

    if bsdf is None:
        raise Exception("Nie znaleziono Principled BSDF")

    # znajdź lub utwórz Image Texture
    image_node = None

    for node in nodes:
        if node.type == 'TEX_IMAGE':
            image_node = node
            break

    if image_node is None:
        image_node = nodes.new("ShaderNodeTexImage")

    # ustaw obraz
    image_node.image = image

    # podłącz do Base Color
    links = mat.node_tree.links

    # usuń stare połączenie Base Color
    for link in list(bsdf.inputs["Base Color"].links):
        links.remove(link)

    links.new(
        image_node.outputs["Color"],
        bsdf.inputs["Base Color"]
    )

if __name__=="__main__":
    canvas_name = "canvas"
    frame_name = "frame"
    glass_name = "glass"
    desc_name = "plakietka"
    idx = random.choice(range(1,1131))
    image_path = f"/home/neerka/blender/projects/visart26/assets/textures/pictures/{idx}.jpg"
    margin = 1.01
    load_picture(canvas_name, frame_name, glass_name, desc_name, image_path, margin)
