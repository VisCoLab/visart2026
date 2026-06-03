"""Robust metadata dumper for Blender scenes.

Only the function `dump_scene_metadata(output_path)` is intended for external use.
This module attempts to resolve values used by Principled BSDF inputs even when
they come from node links or from geometry attributes produced by Geometry Nodes.

Features:
- collect scene, world, objects and materials metadata
- resolve Principled `Base Color` to a concrete RGB when fed by simple RGB/Value/Mix/Combine nodes
- detect Attribute nodes feeding shader inputs and sample/average mesh attributes (colors/scalars)
- record image textures used by nodes
- write YAML (PyYAML) or fallback to JSON
"""

from typing import Any, Optional, Tuple
import json
import os
import sys

try:
    import yaml
    _HAS_YAML = True
except Exception:
    yaml = None
    _HAS_YAML = False

import bpy
from mathutils import Vector, Euler, Matrix, Quaternion


def _to_py(o: Any):
    if o is None:
        return None
    if isinstance(o, (str, int, float, bool)):
        return o
    if isinstance(o, (Vector, Euler, Quaternion)):
        return [float(x) for x in o]
    if isinstance(o, Matrix):
        return [[float(x) for x in row] for row in o]
    try:
        if hasattr(o, '__iter__') and not isinstance(o, (str, bytes, dict)):
            return [_to_py(x) for x in o]
    except Exception:
        pass
    try:
        name = getattr(o, 'name', None)
        if isinstance(name, str):
            return name
    except Exception:
        pass
    try:
        return str(o)
    except Exception:
        return None


def _resolve_socket_value(sock, visited=None):
    """Resolve a socket's constant/default value or follow links once.

    Returns a float or an RGB tuple (r,g,b) or None.
    """
    if visited is None:
        visited = set()
    try:
        if getattr(sock, 'is_linked', False) and getattr(sock, 'links', None):
            link = next(iter(sock.links), None)
            if link and getattr(link, 'from_socket', None):
                return _resolve_socket_value(link.from_socket, visited)
    except Exception:
        return None

    dv = getattr(sock, 'default_value', None)
    if dv is None:
        return None
    if isinstance(dv, (float, int)):
        return float(dv)
    try:
        if hasattr(dv, '__len__') and len(dv) >= 3:
            return tuple(float(x) for x in dv[:3])
    except Exception:
        pass
    return None


def _resolve_node_color_output(from_socket, visited=None) -> Optional[Tuple[float, float, float]]:
    """Attempt to compute RGB for a node output socket for simple node types.

    Supports: ShaderNodeRGB, ShaderNodeValue, ShaderNodeMixRGB, ShaderNodeCombineRGB.
    Falls back to socket default when possible. Does NOT evaluate image textures.
    """
    if visited is None:
        visited = set()
    node = getattr(from_socket, 'node', None)
    if node is None:
        val = _resolve_socket_value(from_socket, visited)
        if isinstance(val, tuple) and len(val) >= 3:
            return tuple(val[:3])
        return None

    node_id = (getattr(node, 'name', None), getattr(node, 'bl_idname', getattr(node, 'type', None)))
    if node_id in visited:
        return None
    visited.add(node_id)

    bname = getattr(node, 'bl_idname', '') or getattr(node, 'type', '')

    # RGB node
    if 'ShaderNodeRGB' in bname or getattr(node, 'type', '') == 'RGB':
        try:
            out = node.outputs[0].default_value
            return tuple(float(x) for x in out[:3])
        except Exception:
            try:
                return tuple(float(x) for x in getattr(node, 'color', ()))
            except Exception:
                return None

    # Value -> gray
    if 'ShaderNodeValue' in bname or getattr(node, 'type', '') == 'VALUE':
        try:
            v = node.outputs[0].default_value
            return (float(v), float(v), float(v))
        except Exception:
            return None

    # MixRGB
    if 'ShaderNodeMixRGB' in bname or getattr(node, 'type', '') in ('MIX_RGB', 'MIX'):
        try:
            inp1 = node.inputs.get('Color1') or node.inputs.get('Color') or (node.inputs[1] if len(node.inputs) > 1 else None)
            inp2 = node.inputs.get('Color2') or (node.inputs[2] if len(node.inputs) > 2 else None)
            fac_in = node.inputs.get('Fac') or node.inputs.get('Factor')
            c1 = _resolve_socket_value(inp1, visited) if inp1 else None
            c2 = _resolve_socket_value(inp2, visited) if inp2 else None
            fac = _resolve_socket_value(fac_in, visited) if fac_in else None
            if c1 and c2:
                if fac is None:
                    fac = 0.5
                fac = float(fac)
                return tuple(max(0.0, min(1.0, c1[i] * (1.0 - fac) + c2[i] * fac)) for i in range(3))
        except Exception:
            return None

    # CombineRGB
    if 'ShaderNodeCombineRGB' in bname or getattr(node, 'type', '') == 'COMBINE_RGB':
        try:
            r = _resolve_socket_value(node.inputs.get('R'), visited)
            g = _resolve_socket_value(node.inputs.get('G'), visited)
            b = _resolve_socket_value(node.inputs.get('B'), visited)
            if r is not None and g is not None and b is not None:
                return (float(r), float(g), float(b))
        except Exception:
            return None

    return None


def _resolve_image_path(image):
    if image is None:
        return None
    path = getattr(image, 'filepath', None)
    if path:
        return path
    return getattr(image, 'name', None)


def _sample_attribute_on_mesh(mesh_obj, attr_name: str, max_samples: int = 16):
    """Sample up to `max_samples` entries from a mesh attribute and return averaged value.

    Returns float or (r,g,b) tuple or None.
    """
    try:
        # color attributes (Blender 3.3+)
        if hasattr(mesh_obj, 'color_attributes'):
            for ca in mesh_obj.color_attributes:
                if ca.name == attr_name:
                    n = len(ca.data)
                    if n == 0:
                        return None
                    samples = min(n, max_samples)
                    acc = [0.0, 0.0, 0.0]
                    count = 0
                    for i in range(samples):
                        try:
                            d = ca.data[i]
                            val = getattr(d, 'color', None) or getattr(d, 'value', None)
                            if val is None:
                                continue
                            rgb = tuple(float(x) for x in val[:3])
                            acc[0] += rgb[0]; acc[1] += rgb[1]; acc[2] += rgb[2]
                            count += 1
                        except Exception:
                            continue
                    if count == 0:
                        return None
                    return (acc[0]/count, acc[1]/count, acc[2]/count)

        # generic attributes
        if hasattr(mesh_obj, 'attributes'):
            for at in mesh_obj.attributes:
                if at.name == attr_name:
                    n = len(at.data)
                    if n == 0:
                        return None
                    samples = min(n, max_samples)
                    accf = 0.0
                    accv = [0.0, 0.0, 0.0]
                    count = 0
                    is_color = False
                    for i in range(samples):
                        try:
                            d = at.data[i]
                            val = getattr(d, 'color', None) or getattr(d, 'vector', None) or getattr(d, 'value', None)
                            if val is None:
                                continue
                            if hasattr(val, '__len__') and len(val) >= 3:
                                is_color = True
                                v = tuple(float(x) for x in val[:3])
                                accv[0] += v[0]; accv[1] += v[1]; accv[2] += v[2]
                            else:
                                accf += float(val)
                            count += 1
                        except Exception:
                            continue
                    if count == 0:
                        return None
                    if is_color:
                        return (accv[0]/count, accv[1]/count, accv[2]/count)
                    return accf / count
    except Exception:
        return None
    return None


def _find_attribute_value_for_material(mat: bpy.types.Material, attr_name: str, max_samples: int = 16):
    """Search objects that use `mat` and return averaged attribute value if present."""
    try:
        # iterate objects and sample first matching mesh attribute
        for obj in bpy.data.objects:
            if obj.type != 'MESH' or not getattr(obj, 'data', None):
                continue
            mesh_obj = obj.data
            try:
                mat_names = [mat_slot.name if mat_slot else None for mat_slot in getattr(mesh_obj, 'materials', [])]
            except Exception:
                mat_names = []
            if mat.name not in mat_names:
                continue
            val = _sample_attribute_on_mesh(mesh_obj, attr_name, max_samples=max_samples)
            if val is not None:
                return val
        return None
    except Exception:
        return None


def _gather_material_details(m: bpy.types.Material):
    info = {'name': m.name, 'use_nodes': bool(getattr(m, 'use_nodes', False)), 'properties': {}, 'textures': []}
    try:
        if not getattr(m, 'use_nodes', False):
            info['properties']['diffuse_color'] = _to_py(getattr(m, 'diffuse_color', None))
            return info

        nt = getattr(m, 'node_tree', None)
        if not nt:
            return info

        # find Principled node
        principled = None
        for node in nt.nodes:
            if getattr(node, 'type', '') == 'BSDF_PRINCIPLED' or getattr(node, 'bl_idname', '') == 'ShaderNodeBsdfPrincipled':
                principled = node
                break

        # collect image textures
        try:
            for node in nt.nodes:
                if getattr(node, 'type', '') == 'TEX_IMAGE':
                    img = getattr(node, 'image', None)
                    info['textures'].append({'node': node.name, 'image': _resolve_image_path(img)})
        except Exception:
            pass

        if principled:
            # Base Color
            try:
                base_in = principled.inputs.get('Base Color') or (principled.inputs[0] if principled.inputs else None)
                if base_in:
                    if getattr(base_in, 'is_linked', False) and getattr(base_in, 'links', None):
                        link = base_in.links[0]
                        from_sock = getattr(link, 'from_socket', None)
                        # image texture?
                        node = getattr(from_sock, 'node', None)
                        if node and getattr(node, 'type', '') == 'TEX_IMAGE':
                            info['textures'].append({'slot': 'Base Color', 'image': _resolve_image_path(getattr(node, 'image', None))})
                        else:
                            # try to resolve simple node outputs
                            resolved = _resolve_node_color_output(from_sock)
                            if resolved is not None:
                                info['properties']['resolved_base_color'] = _to_py(resolved)
                            else:
                                # attribute node detection: record attribute name and sample
                                attr_name = None
                                if node is not None:
                                    for key in ('attribute_name', 'attribute', 'name'):
                                        val = getattr(node, key, None)
                                        if isinstance(val, str) and val:
                                            attr_name = val
                                            break
                                    if not attr_name:
                                        try:
                                            inp = node.inputs.get('Attribute') or node.inputs.get('Name')
                                            if inp:
                                                dv = getattr(inp, 'default_value', None)
                                                if isinstance(dv, str) and dv:
                                                    attr_name = dv
                                        except Exception:
                                            pass
                                if attr_name:
                                    info['properties']['attribute'] = attr_name
                                    val = _find_attribute_value_for_material(m, attr_name)
                                    if val is not None:
                                        info['properties']['attribute_value'] = _to_py(val)
                                else:
                                    info['properties']['base_color_link'] = getattr(node, 'name', str(node)) if node else str(from_sock)
                    else:
                        info['properties']['base_color'] = _to_py(getattr(base_in, 'default_value', None))
            except Exception:
                pass

            # Metallic
            try:
                metallic = principled.inputs.get('Metallic')
                if metallic:
                    if getattr(metallic, 'is_linked', False) and getattr(metallic, 'links', None):
                        link = metallic.links[0]
                        from_sock = getattr(link, 'from_socket', None)
                        node = getattr(from_sock, 'node', None)
                        attr_name = None
                        if node is not None:
                            for key in ('attribute_name', 'attribute', 'name'):
                                val = getattr(node, key, None)
                                if isinstance(val, str) and val:
                                    attr_name = val
                                    break
                            if not attr_name:
                                try:
                                    inp = node.inputs.get('Attribute') or node.inputs.get('Name')
                                    if inp:
                                        dv = getattr(inp, 'default_value', None)
                                        if isinstance(dv, str) and dv:
                                            attr_name = dv
                                except Exception:
                                    pass
                        if attr_name:
                            info['properties']['metallic_attribute'] = attr_name
                            val = _find_attribute_value_for_material(m, attr_name)
                            if val is not None:
                                info['properties']['metallic'] = _to_py(val)
                            else:
                                info['properties']['metallic'] = float(getattr(metallic, 'default_value', 0.0))
                        else:
                            info['properties']['metallic'] = float(getattr(metallic, 'default_value', 0.0))
                    else:
                        info['properties']['metallic'] = float(getattr(metallic, 'default_value', 0.0))
            except Exception:
                pass

            # Roughness
            try:
                rough = principled.inputs.get('Roughness')
                if rough:
                    if getattr(rough, 'is_linked', False) and getattr(rough, 'links', None):
                        link = rough.links[0]
                        from_sock = getattr(link, 'from_socket', None)
                        node = getattr(from_sock, 'node', None)
                        attr_name = None
                        if node is not None:
                            for key in ('attribute_name', 'attribute', 'name'):
                                val = getattr(node, key, None)
                                if isinstance(val, str) and val:
                                    attr_name = val
                                    break
                            if not attr_name:
                                try:
                                    inp = node.inputs.get('Attribute') or node.inputs.get('Name')
                                    if inp:
                                        dv = getattr(inp, 'default_value', None)
                                        if isinstance(dv, str) and dv:
                                            attr_name = dv
                                except Exception:
                                    pass
                        if attr_name:
                            info['properties']['roughness_attribute'] = attr_name
                            val = _find_attribute_value_for_material(m, attr_name)
                            if val is not None:
                                info['properties']['roughness'] = _to_py(val)
                            else:
                                info['properties']['roughness'] = float(getattr(rough, 'default_value', 0.0))
                        else:
                            info['properties']['roughness'] = float(getattr(rough, 'default_value', 0.0))
                    else:
                        info['properties']['roughness'] = float(getattr(rough, 'default_value', 0.0))
            except Exception:
                pass

    except Exception:
        pass

    return info


def _gather_object(obj: bpy.types.Object):
    data = {
        'name': obj.name,
        'type': obj.type,
        'location': _to_py(getattr(obj, 'location', None)),
        'rotation_euler': _to_py(getattr(obj, 'rotation_euler', None)),
        'scale': _to_py(getattr(obj, 'scale', None)),
    }
    try:
        if obj.type == 'MESH' and getattr(obj, 'data', None):
            mesh = obj.data
            mats = [m.name for m in getattr(mesh, 'materials', []) if m]
            data['mesh'] = {
                'name': getattr(mesh, 'name', None),
                'vertices_count': len(mesh.vertices) if hasattr(mesh, 'vertices') else None,
                'polygons_count': len(mesh.polygons) if hasattr(mesh, 'polygons') else None,
                'materials': mats,
            }
            # collect available attribute names (color_attributes / attributes)
            attrs = []
            try:
                if hasattr(mesh, 'color_attributes'):
                    for ca in mesh.color_attributes:
                        attrs.append({'name': ca.name, 'domain': getattr(ca, 'domain', None), 'data_type': getattr(ca, 'data_type', None)})
                elif hasattr(mesh, 'attributes'):
                    for at in mesh.attributes:
                        attrs.append({'name': at.name, 'domain': getattr(at, 'domain', None), 'data_type': getattr(at, 'data_type', None)})
            except Exception:
                pass
            if attrs:
                data['mesh']['attributes'] = attrs
    except Exception:
        pass
    return data


def dump_scene_metadata(output_path: str):
    """Collect metadata from the current Blender scene and write it to `output_path`.

    The output is YAML when PyYAML is available, otherwise JSON.
    """
    scene = bpy.context.scene
    view_layer = bpy.context.view_layer

    out = {
        'scene': {
            'name': getattr(scene, 'name', None),
            'frame_start': int(getattr(scene, 'frame_start', 0)),
            'frame_end': int(getattr(scene, 'frame_end', 0)),
            'render': {
                'engine': getattr(scene.render, 'engine', None),
                'resolution_x': int(getattr(scene.render, 'resolution_x', 0)),
                'resolution_y': int(getattr(scene.render, 'resolution_y', 0)),
                'fps': int(getattr(scene.render, 'fps', 0)) if hasattr(scene.render, 'fps') else None,
            },
        },
        'world': None,
        'objects': [],
        'materials': [],
    }

    try:
        w = getattr(scene, 'world', None)
        if w:
            out['world'] = {'name': getattr(w, 'name', None), 'use_nodes': bool(getattr(w, 'use_nodes', False)), 'color': _to_py(getattr(w, 'color', None))}
    except Exception:
        pass

    # only include objects visible in the current view layer
    visible_objs = []
    try:
        for obj in bpy.data.objects:
            try:
                if obj.visible_get(view_layer):
                    visible_objs.append(obj)
            except Exception:
                # fallback: include if not hidden in viewport
                if not getattr(obj, 'hide_viewport', False):
                    visible_objs.append(obj)
    except Exception:
        visible_objs = []

    try:
        for obj in visible_objs:
            out['objects'].append(_gather_object(obj))
    except Exception:
        pass

    # collect materials used by visible objects only
    used_mats = []
    try:
        seen = set()
        for obj in visible_objs:
            if obj.type == 'MESH' and getattr(obj, 'data', None):
                mesh = obj.data
                for m in getattr(mesh, 'materials', []):
                    if m and m.name not in seen:
                        seen.add(m.name)
                        used_mats.append(m)
    except Exception:
        used_mats = []

    try:
        for m in used_mats:
            out['materials'].append(_gather_material_details(m))
    except Exception:
        pass

    # scene custom props
    try:
        props = {}
        for k, v in scene.items():
            if k.startswith('_'):
                continue
            props[k] = _to_py(v)
        if props:
            out['scene']['custom_properties'] = props
    except Exception:
        pass

    # ensure directory
    dirname = os.path.dirname(output_path)
    if dirname and not os.path.exists(dirname):
        try:
            os.makedirs(dirname, exist_ok=True)
        except Exception:
            pass

    if _HAS_YAML:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(out, f, default_flow_style=False, allow_unicode=True)
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, ensure_ascii=False)


__all__ = ['dump_scene_metadata']
