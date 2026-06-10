import bpy

def _turnoff_gn_randomization(obj: object):
    gn_modifier = obj.modifiers["GeometryNodes"]
    node_tree = gn_modifier.node_group

    to_remove = [
        n for n in node_tree.nodes if n.bl_idname == "GeometryNodeInputSceneTime"
    ]

    for n in to_remove:
        node_tree.nodes.remove(n)


def _turnoff_gn_randomization_by_name(obj: object, node_names: list[str]):
    gn_modifier = obj.modifiers["GeometryNodes"]
    node_tree = gn_modifier.node_group

    # match node labels as well as names: labels are what the UI shows and what
    # the scene author sets (e.g. the 'Frame' Scene Time node in GEO_Paint)
    to_remove = [
        n for n in node_tree.nodes
        if n.bl_idname == "GeometryNodeInputSceneTime"
        and (n.name in node_names or n.label in node_names)
    ]

    for n in to_remove:
        node_tree.nodes.remove(n)


def stale_floor_walls():
    wall = bpy.data.objects["Wall"]
    floor = bpy.data.objects["Floor"]
    roof = bpy.data.objects["Roof"]

    _turnoff_gn_randomization(wall)
    _turnoff_gn_randomization(floor)
    _turnoff_gn_randomization(roof)


def stale_lights():
    lights = bpy.data.objects["Light instanced"]

    _turnoff_gn_randomization(lights)


def stale_painting_frame():
    painting = bpy.data.objects["Painting instanced"]
    frame = bpy.data.objects["frame"]
    
    _turnoff_gn_randomization_by_name(painting, ["Frame"])
    _turnoff_gn_randomization(frame)


def set_glass_probability(threshold: float):
    threshold = 1.0 if threshold > 1.0 else (0.0 if threshold < 0.0 else threshold)

    obj = bpy.data.objects["Painting instanced"]
    gn_modifier = obj.modifiers["GeometryNodes"]
    node_tree = gn_modifier.node_group

    target_node = None
    for node in node_tree.nodes:
        if node.bl_idname == "ShaderNodeMath":
            target_node = node
    
    target_node.inputs[1].default_value = 1.0 - threshold

if __name__=='__main__':
    set_glass_probability(0.5)



