import bpy
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from placard_resetter import reset_placard

def load_picture(frame_idx: int,
                 canvas_name: str,
                 frame_name: str,
                 glass_name: str,
                 desc_name: str,
                 image_path: str,
                 margin: float):
    # ===== GET OBJECTS =====

    obj = bpy.data.objects[canvas_name]
    frame = bpy.data.objects[frame_name]
    glass = bpy.data.objects[glass_name]
    placard = bpy.data.objects[desc_name]

    # ===== LOAD IMAGE =====

    image = bpy.data.images.load(image_path, check_existing=True)

    # ===== SCALE THE CANVAS =====

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

    reset_placard(canvas_name, desc_name, margin, frame_idx)

    # ===== MATERIAL =====

    mat = obj.active_material

    if mat is None:
        mat = bpy.data.materials.new("CanvasMaterial")
        mat.use_nodes = True
        obj.active_material = mat

    mat.use_nodes = True

    nodes = mat.node_tree.nodes

    # find Principled BSDF
    bsdf = nodes.get("Principled BSDF")

    if bsdf is None:
        raise Exception("Principled BSDF not found")

    # find or create Image Texture
    image_node = None

    for node in nodes:
        if node.type == 'TEX_IMAGE':
            image_node = node
            break

    if image_node is None:
        image_node = nodes.new("ShaderNodeTexImage")

    # set the image
    image_node.image = image

    # connect to Base Color
    links = mat.node_tree.links

    # remove the old Base Color connection
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
    desc_name = "plakietka"  # .blend object name (kept to match the scene)
    assets = Path(__file__).resolve().parent.parent / "assets"
    image_path = str(assets / "textures" / "plk.png")
    margin = 1.01
    load_picture(canvas_name, frame_name, glass_name, desc_name, image_path, margin)
