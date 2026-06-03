import bpy
import math

# =====================================
# CONFIG
# =====================================

COLLECTION_NAME = "FrameVariants"

OUTER_SIZE = 2.0
INNER_SIZE = 1.5

# =====================================
# CLEAN
# =====================================

if COLLECTION_NAME in bpy.data.collections:
    col = bpy.data.collections[COLLECTION_NAME]

    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    col = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(col)

# =====================================
# FRAME PATH
# =====================================

def create_rectangle_curve(name, outer):

    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'

    spline = curve.splines.new('POLY')
    spline.points.add(3)

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
    spline.points.add(len(points)-1)

    for p, v in zip(spline.points, points):
        p.co = (*v, 0, 1)

    spline.use_cyclic_u = True

    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)

    return obj


# =====================================
# PROFILE LIBRARY
# =====================================

profiles = [

    # 0 flat
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.15, 0.08),
        (0.00, 0.08),
    ],

    # 1 bevel
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.15, 0.08),
        (0.05, 0.12),
        (0.00, 0.08),
    ],

    # 2 reverse bevel
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.12, 0.10),
        (0.03, 0.12),
        (0.00, 0.08),
    ],

    # 3 museum convex
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.18, 0.05),
        (0.15, 0.10),
        (0.08, 0.14),
        (0.00, 0.08),
    ],

    # 4 stepped
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

    # 5 deep recess
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.15, 0.15),
        (0.08, 0.18),
        (0.00, 0.08),
    ],

    # 6 decorative
    [
        (0.00, 0.00),
        (0.06, 0.00),
        (0.08, 0.04),
        (0.12, 0.06),
        (0.15, 0.10),
        (0.00, 0.12),
    ],

    # 7 wide decorative
    [
        (0.00, 0.00),
        (0.20, 0.00),
        (0.18, 0.05),
        (0.22, 0.08),
        (0.15, 0.15),
        (0.00, 0.10),
    ],

    # 8 groove
    [
        (0.00, 0.00),
        (0.15, 0.00),
        (0.15, 0.08),
        (0.10, 0.08),
        (0.10, 0.04),
        (0.05, 0.04),
        (0.05, 0.10),
        (0.00, 0.10),
    ],

    # 9 baroque-ish
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
# BUILD FRAMES
# =====================================

for idx, profile in enumerate(profiles):

    path = create_rectangle_curve(
        f"FramePath_{idx}",
        OUTER_SIZE
    )

    prof = profile_curve(
        f"FrameProfile_{idx}",
        profile
    )

    path.data.bevel_mode = 'OBJECT'
    path.data.bevel_object = prof

    bpy.context.view_layer.objects.active = path
    path.select_set(True)

    bpy.ops.object.convert(target='MESH')

    frame = bpy.context.active_object
    frame.name = f"frame{3+idx:02d}"

    frame.location.x = idx * 3

    col.objects.link(frame)

    for c in frame.users_collection:
        if c != col:
            c.objects.unlink(frame)

    bpy.data.objects.remove(prof, do_unlink=True)

print("Done.")