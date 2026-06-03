"""Enable Cycles GPU rendering in a headless Blender session.

Headless Blender does not enable GPU compute devices on its own, so this must
run BEFORE the render script, in the same Blender invocation:

    blender -b scene.blend --python enable_gpu.py --python main.py -- ...

It prefers CUDA (reliable across driver versions on this cluster — OptiX
segfaults on the tesla nodes due to a driver/RT-core version skew), falls
back to OptiX, enables every detected GPU of that backend, and switches all
scenes to GPU. If no GPU backend is available it leaves the device settings
untouched (so CPU rendering still works).
"""
import bpy


def enable_gpu():
    prefs = bpy.context.preferences.addons['cycles'].preferences

    chosen = None
    for backend in ('CUDA', 'OPTIX'):
        try:
            prefs.compute_device_type = backend
        except TypeError:
            continue  # backend not compiled into this build
        try:
            prefs.refresh_devices()
        except AttributeError:
            prefs.get_devices()
        if any(d.type == backend for d in prefs.devices):
            chosen = backend
            break

    if chosen is None:
        print("ENABLE_GPU: no GPU backend found; leaving render device unchanged")
        return

    enabled = 0
    for d in prefs.devices:
        d.use = (d.type == chosen)
        if d.use:
            enabled += 1
            print(f"ENABLE_GPU: enabled {d.type} device: {d.name}")

    for scene in bpy.data.scenes:
        scene.cycles.device = 'GPU'

    print(f"ENABLE_GPU: backend={chosen}, gpus_enabled={enabled}")


if __name__ == "__main__":
    enable_gpu()
