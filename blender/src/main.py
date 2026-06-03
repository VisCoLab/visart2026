import bpy
import argparse
import os
import random
import sys
sys.path.append("/home/neerka/blender/projects/visart26/assets/scripts")

from camera_settings import (
    reset_cameras, 
    get_original_settings, 
    move_cameras)
from frame_loader import load_picture
from floor_setter import reset_floor
from mod_lights import mod_lights
from metadata_handler import dump_scene_metadata

def parse_cli_args():
    parser = argparse.ArgumentParser(description='Parser for rendering/data parameters')
    parser.add_argument('--render-frames', nargs=2, type=int, metavar=('START', 'END'),
                        help='Frame range to render as two integers: START END', required=True)
    parser.add_argument('--fpd', type=int, default=1, help='Frames per datapoint (int)')
    parser.add_argument('--render-mode', nargs='+', choices=('rgb', 'mask', 'depth'), default=['rgb'],
                        help='Render modes to perform: one or more of rgb, mask, depth')
    parser.add_argument('--data-path', type=str, required=True, help='Path to input images')
    parser.add_argument('--save-path', type=str, required=True, help='Path to save outputs')
    parser.add_argument('--data-index', type=int, default=0, help='Start index (0-based) of files in data-path to load')
    parser.add_argument('--margin', type=float, default=1.01,
                        help='Margin between image and frame (float), default 1.01')
    parser.add_argument('--light-shape', choices=('square', 'disk', 'random'), default='random',
                        help='Shape of lights in scene: square, disk or random (default)')
    parser.add_argument('--light-spread', nargs=2, type=int, metavar=('MIN', 'MAX'), default=(60, 180),
                        help='Range (MIN MAX) in degrees for random light spread (default 60 180)')
    parser.add_argument('--render-resolution', nargs=2, type=int, metavar=('W', 'H'), default=(1920, 1080),
                        help='Render resolution to save images as two integers: WIDTH HEIGHT')

    argv = sys.argv
    if '--' in argv:
        cli = argv[argv.index('--') + 1:]
    else:
        cli = None
        for i, a in enumerate(argv):
            if a.endswith('main.py') or a.endswith('/main.py'):
                cli = argv[i+1:]
                break
        if cli is None:
            cli = argv[1:]
    args = parser.parse_args(cli)

    # Normalize render_frames to a tuple (start, end)
    start, end = args.render_frames
    if start > end:
        parser.error('render-frames START must be <= END')
    if args.data_index < 0:
        parser.error('data-index must be >= 0')

    # normalize light_spread
    ls_min, ls_max = args.light_spread
    if ls_min > ls_max:
        parser.error('light-spread MIN must be <= MAX')

    # render resolution validation
    render_res = None
    if args.render_resolution is not None:
        rw, rh = args.render_resolution
        if rw <= 0 or rh <= 0:
            parser.error('render-resolution WIDTH and HEIGHT must be positive integers')
        render_res = (int(rw), int(rh))

    return {
        'render_frames': (start, end),
        'fpd': args.fpd,
        'render_mode': tuple(args.render_mode),
        'data_path': os.path.abspath(args.data_path),
        'save_path': os.path.abspath(args.save_path),
        'data_index': args.data_index,
        'margin': args.margin,
        'light_shape': args.light_shape,
        'light_spread': (int(ls_min), int(ls_max)),
        'render_resolution': render_res,
    }

if __name__=="__main__":
    args = parse_cli_args()

    # DATA SETUP
    START, END = args["render_frames"]
    FPD = args['fpd']
    renders = args['render_mode']
    data_path = args["data_path"]
    save_path = args["save_path"]
    did = args['data_index']
    margin = args['margin']
    l_shape = args['light_shape']
    spread_min, spread_max = args['light_spread']
    res_x, res_y = args['render_resolution']

    light_shapes = ["SQUARE", "DISK"] if l_shape=='random' else [l_shape.upper()]

    canvas_name = "canvas"
    frame_name = "frame"
    glass_name = "glass"
    desc_name = "plakietka"

    cameras = bpy.data.collections.get("Cameras")

    # READ DATASET PATH
    if not os.path.isdir(data_path):
        raise SystemExit(f'data-path does not exist or is not a directory: {data_path}')

    all_files = [f for f in os.listdir(data_path) if not f.startswith('.') and os.path.isfile(os.path.join(data_path, f))]
    data_files = sorted(all_files, key=lambda x: x.lower())
    data_files_full = [os.path.join(data_path, f) for f in data_files]

    print(f'Found {len(all_files)} files in data-path')

    image_path = data_files_full[did]

    # SAVE CAMERA INFO FOR LATER
    og_cameras = get_original_settings()

    scene = bpy.context.scene
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    
    # LOOP SETUP
    counter = 1
    load_picture(canvas_name,
                 frame_name,
                 glass_name,
                 desc_name,
                 image_path,
                 margin)

    for frame in range(START, END+1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        shape = random.choice(light_shapes)
        spread = random.choice([_ for _ in range(spread_min,spread_max)])
        mod_lights(shape, spread)
        reset_floor('Ground')
        move_cameras()

        if counter % FPD == 0:
            did += 1
            image_path = data_files_full[did]
            load_picture(canvas_name, 
                         frame_name, 
                         glass_name,
                         desc_name,
                         image_path,
                         margin)
        
        save_folder = os.path.join(save_path, f'{counter//FPD}')
        for comp in renders:
            for camera in cameras.objects:
                bpy.context.scene.camera = camera
                bpy.context.scene.compositing_node_group = bpy.data.node_groups[comp]
                filename = f'{counter%FPD}'+"_"+comp+f'_{camera.name}'+".png"
                bpy.data.scenes["Scene"].render.filepath = os.path.join(save_folder, filename)
                bpy.data.scenes["Scene"].render.image_settings.file_format = "PNG"
                bpy.ops.render.render(write_still=True)
        dump_scene_metadata(os.path.join(save_folder,'metadata.json'))

        reset_cameras(og_cameras)
        print(f"Rendered datapoint {counter//FPD}, frame: {counter%FPD}")
        counter += 1




