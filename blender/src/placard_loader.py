import bpy
from pathlib import Path

def load_placard(obj_name: str,
                 image_path: str):
    obj = bpy.data.objects[obj_name]
    image = bpy.data.images.load(image_path, check_existing=True)

    w = image.size[0]
    h = image.size[1]
    scale = 0.15

    aspect = w / h

    if aspect >= 1:
        obj.scale.x = aspect * scale
        obj.scale.y = 1 * scale
    else:
        obj.scale.x = 1 * scale
        obj.scale.y = 1 / aspect * scale

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

if __name__ == "__main__":
    obj_name = "plakietka"  # .blend object name (kept to match the scene)
    assets = Path(__file__).resolve().parent.parent / "assets"
    image_path = str(assets / "textures" / "plk.png")
    load_placard(obj_name, image_path)
