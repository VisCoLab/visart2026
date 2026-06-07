# Running `main.py`

This script is meant to run in Blender's headless context (no GUI). It takes arguments via `argparse` — Blender passes any extra arguments after the `--` separator.

**Headless invocation (example)**

```bash
blender -b scene.blend --python /path/to/main.py -- [ARGUMENTS]
```

Instead of `scene.blend` you can pass your own `.blend` file, or run Blender without a file if the script builds the scene itself.

**Available arguments**

- `--render-frames START END` : frame range to render; two integers (START, END). START must be <= END.
	- Example: `--render-frames 1 100`

- `--fpd N` : frames per datapoint — how many frames belong to one datapoint (int). Defaults to `1`.
	- Example: `--fpd 2`

- `--render-mode MODE [MODE ...]` : render modes; one or more of `rgb`, `mask`, `depth`. The script runs every mode given.
	- Single-mode example: `--render-mode rgb`
	- Multi-mode example: `--render-mode rgb mask depth`

- `--data-path PATH` : directory of input images, **or** a `.json` manifest file holding a list of image paths (consumed in the order given).
	- Directory example: `--data-path ./data/images`
	- Manifest example: `--data-path ./data/paintings_train_images.json`

- `--save-path PATH` : path where results are written (e.g. images, metadata).
	- Example: `--save-path ./out`

- `--data-index N` : 0-based index of the file in `--data-path` at which loading starts.
	- Example: `--data-index 5` — the script starts from the sixth file in the directory.

- `--margin F` : margin between the image and the picture frame (float). Defaults to `1.01`.
	- Example: `--margin 1.02`

- `--light-shape SHAPE` : shape of the light sources; one of `square`, `disk`, `random` (default `random`).
	- Example: `--light-shape square`

- `--light-spread MIN MAX` : range (in degrees) from which the light spread angle is drawn, from MIN to MAX. Defaults to `60 180`.
	- Example: `--light-spread 45 120`

- `--render-resolution WIDTH HEIGHT` : resolution at which renders are saved (two ints: width and height).
	- Example: `--render-resolution 1024 768`

- `--camera-modifiers MOD [MOD ...]` : which camera modifiers to apply; one or both of `translation` and `rotation`. When `translation` is present, camera translation jitter is applied (using `--trans-y`/`--trans-z`). When `rotation` is present, camera rotation jitter is applied (using `--rot-range`). Defaults to both `translation` and `rotation`.
	- Example: `--camera-modifiers translation rotation`

- `--trans-y F` : translation magnitude along the camera Y axis used when camera translation is enabled (float). Defaults to `0.6`.
	- Example: `--trans-y 0.6`

- `--trans-z F` : translation magnitude along the camera Z axis used when camera translation is enabled (float). Defaults to `0.2`.
	- Example: `--trans-z 0.2`

- `--rot-range F` : rotation range (in degrees) used when camera rotation is enabled; rotations are sampled within ±F degrees. Defaults to `5.0`.
	- Example: `--rot-range 5.0`

NOTE: When you run the script via `blender --python`, all script arguments must be given after the `--` separator, e.g. `-- --render-frames 1 10`.

**Usage examples**

- Render frames 1–100, modes `rgb` and `mask`, save to `./out`, load data from `./data` starting at index 5, 2 frames per datapoint:

```bash
blender -b scene.blend --python /path/to/main.py -- \
	--render-frames 1 100 --fpd 2 --render-mode rgb mask --data-path ./data --save-path ./out --data-index 5 \
	--margin 1.02 --light-shape square --light-spread 45 120 --render-resolution 1024 768
```

- Simple example with the default `fpd` and a single mode:

```bash
blender -b scene.blend --python /path/to/main.py -- \
	--render-frames 10 10 --render-mode rgb --data-path /mnt/images --save-path /mnt/save
```

**Help / debug**

To see the description of all arguments:

```bash
blender -b --python /path/to/main.py -- --help
```

`main.py` exports a `parse_cli_args()` function that normalizes values (e.g. a tuple for `render_frames`, a tuple for `render_mode`, absolute paths for `data_path` and `save_path`) — use it in your script to get the already-parsed settings.
