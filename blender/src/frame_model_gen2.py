import bpy

# =====================================
# CONFIG
# =====================================

COLLECTION_NAME = "Frames_WIP"
MATERIAL_NAME = "Frame"

OUTER_SIZE = 2.0
FRAME_WIDTHS = [0.15, 0.3, 0.5]

# =====================================
# MATERIAL
# =====================================

material = bpy.data.materials.get(MATERIAL_NAME)

if material is None:
    raise Exception(
        f"Material '{MATERIAL_NAME}' does not exist."
    )

# =====================================
# CLEAN COLLECTION
# =====================================

if COLLECTION_NAME in bpy.data.collections:
    col = bpy.data.collections[COLLECTION_NAME]

    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    col = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(col)

# =====================================
# RECTANGLE PATH
# =====================================

def create_rectangle_curve(name, outer, frame_width):

    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'

    spline = curve.splines.new('POLY')
    spline.points.add(3)

    offset = frame_width * 0.5

    pts = [
        (-outer/2, -outer/2, 0),
        ( outer/2, -outer/2, 0),
        ( outer/2,  outer/2, 0),
        (-outer/2,  outer/2, 0),
    ]

    for p, v in zip(spline.points, pts):
        p.co = (*v, 1)

    spline.use_cyclic_u = True

    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)

    return obj

# =====================================
# PROFILE CREATOR
# =====================================

def profile_curve(name, points):

    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '2D'

    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)

    for p, v in zip(spline.points, points):
        p.co = (*v, 0, 1)

    spline.use_cyclic_u = True

    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)

    return obj

# =====================================
# PROFILES
# =====================================

profiles = [

    # 0 Flat
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.15, 0.08),
        (0.00, 0.08),
    ],

    # 1 Bevel
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.15, 0.08),
        (0.05, 0.12),
        (0.00, 0.08),
    ],

    # 2 Reverse Bevel
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.12, 0.10),
        (0.03, 0.12),
        (0.00, 0.08),
    ],

    # 3 Museum Convex
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.18, 0.05),
        (0.15, 0.10),
        (0.08, 0.14),
        (0.00, 0.08),
    ],

    # 4 Stepped
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.15, 0.04),
        (0.10, 0.04),
        (0.10, 0.08),
        (0.05, 0.08),
        (0.05, 0.12),
        (0.00, 0.12),
    ],

    # 5 Deep Recess
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.15, 0.15),
        (0.08, 0.18),
        (0.00, 0.08),
    ],

    # 6 Decorative
    [
        (0.00, 0.00),
        (0.06, 0.00),
        (0.08, 0.04),
        (0.12, 0.06),
        (0.15, 0.10),
        (0.00, 0.12),
    ],

    # 7 Wide Decorative
    [
        (0.00, 0.00),
        (0.20, 0.00),
        (0.18, 0.05),
        (0.22, 0.08),
        (0.15, 0.15),
        (0.00, 0.10),
    ],

    # # 8 Groove
    # [
    #     (0.00, 0.00),
    #     (0.15, 0.00),
    #     (0.15, 0.08),
    #     (0.10, 0.08),
    #     (0.10, 0.04),
    #     (0.05, 0.04),
    #     (0.05, 0.10),
    #     (0.00, 0.10),
    # ],

    # 9 Baroque-ish
    [
        (0.00, 0.00),
        (0.06, 0.00),
        (0.08, 0.03),
        (0.12, 0.06),
        (0.18, 0.10),
        (0.14, 0.16),
        (0.00, 0.12),
    ],
]

# =====================================
# GENERATE
# =====================================

for idx, profile in enumerate(profiles):
    for off, width in enumerate(FRAME_WIDTHS):
        profile_scale = width / 0.15
        _id = 3*idx + off
        path = create_rectangle_curve(
            f"FramePath_{_id}",
            OUTER_SIZE,
            width
        )

        scaled_profile = [
            (x * profile_scale, y)
            for x, y in profile
        ]

        prof = profile_curve(
            f"FrameProfile_{_id}",
            scaled_profile
        )

        path.data.bevel_mode = 'OBJECT'
        path.data.bevel_object = prof

        bpy.context.view_layer.objects.active = path
        path.select_set(True)

        bpy.ops.object.convert(target='MESH')

        frame = bpy.context.active_object
        frame.name = f"frame{_id:02d}"

        # =================================
        # MATERIAL
        # =================================

        frame.data.materials.clear()
        frame.data.materials.append(material)

        # =================================
        # SMOOTH
        # =================================

        bpy.ops.object.shade_smooth()

        bevel = frame.modifiers.new(
            name="Bevel",
            type='BEVEL'
        )

        bevel.width = 0.003
        bevel.segments = 3

        weighted = frame.modifiers.new(
            name="WeightedNormal",
            type='WEIGHTED_NORMAL'
        )

        bpy.context.view_layer.objects.active = frame

        bpy.ops.object.modifier_apply(
            modifier=bevel.name
        )

        bpy.ops.object.modifier_apply(
            modifier=weighted.name
        )

        frame.location.x = _id * 3

        col.objects.link(frame)

        for c in frame.users_collection:
            if c != col:
                c.objects.unlink(frame)

        bpy.data.objects.remove(
            prof,
            do_unlink=True
        )


print("Generated 30 frame variants.")