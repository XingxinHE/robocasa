# Dataset Scripts Runbook

## Overview

The original RoboCasa dataset lifecycle has three stages:

```
collect_demos.py                  -- Teleoperate and record MuJoCo states + actions
        ↓
dataset_states_to_obs.py          -- Re-simulate states to render camera images
        ↓
convert_hdf5_lerobot.py           -- Convert HDF5 images to LeRobot format
```

LeRobot datasets store per-episode raw states in `extras/episode_XXXXXX/states.npz`
so they can be re-rendered later without re-collecting demonstrations.

## Re-exporting Datasets with Modified Camera Configs

If you have changed camera extrinsics in
`robocasa/utils/camera_utils.py` (e.g., `robot0_agentview_left` or
`robot0_agentview_right` positions/rotations) and want to regenerate a LeRobot
dataset with the new camera views, follow this workflow.

Follow the following steps or use the `robocasa_to_hdf5_rerender_lerobot.sh`

### 1. Reconstruct raw HDF5 from LeRobot extras

```bash
uv run --group robocasa python third_party/robocasa/robocasa/scripts/dataset_scripts/lerobot_extras_to_hdf5.py \
    --dataset /path/to/datasets/<Task>/<split>/lerobot

# Example:
uv run --group robocasa python third_party/robocasa/robocasa/scripts/dataset_scripts/lerobot_extras_to_hdf5.py \
    --dataset /data/robocasa/dataset/v1.0/pretrain/atomic/TurnOnMicrowave/20250819/lerobot \
    --output /data/robocasa/dataset/v1.0/pretrain/atomic/TurnOnMicrowave/20260425/reconstructed.hdf5
```

This produces `<dataset_parent>/reconstructed.hdf5` — a raw HDF5 with
states, actions, and metadata (no images). Specify `--output` to use a
different path.

### 2. Re-render images and convert to LeRobot

```bash
uv run --group robocasa python third_party/robocasa/robocasa/scripts/dataset_scripts/convert_hdf5_lerobot.py \
    --raw_dataset_path /path/to/reconstructed.hdf5 \
    --camera_names robot0_agentview_left robot0_agentview_right robot0_eye_in_hand \
    --camera_height 256 --camera_width 256

# Example:
uv run --group robocasa python third_party/robocasa/robocasa/scripts/dataset_scripts/convert_hdf5_lerobot.py \
    --raw_dataset_path /data/robocasa/dataset/v1.0/pretrain/atomic/TurnOnMicrowave/20260425/reconstructed.hdf5 \
    --camera_names robot0_agentview_left robot0_agentview_right robot0_eye_in_hand \
    --camera_height 256 --camera_width 256 \
    --use_cotraining_cameras
```

This creates a new `lerobot/` directory alongside the HDF5 with re-rendered
videos. The old `lerobot/` at that location is replaced.

If you want to use `COTRAIN_CAM_CONFIGS` instead of `CAM_CONFIGS`, add:

```bash
    --use_cotraining_cameras
```

### Batch processing all datasets

To re-export all datasets for a split / source combination, loop over the
dataset registry:

```python
from robocasa.utils.dataset_registry import get_ds_soup

ds_soup = get_ds_soup(task_soup="atomic_seen", split="target", source="human")
for ds_meta in ds_soup:
    ds_path = ds_meta["path"]
    # run lerobot_extras_to_hdf5.py --dataset <ds_path>
    # run convert_hdf5_lerobot.py --raw_dataset_path <output_hdf5>
```

## Camera Configurations

Camera extrinsics are defined in `robocasa/utils/camera_utils.py`:

| Dict              | Used when                          |
|-------------------|------------------------------------|
| `CAM_CONFIGS`     | Default (`use_cotraining_cameras=False`) |
| `COTRAIN_CAM_CONFIGS` | `use_cotraining_cameras=True`  |

The environment reads its camera config from the current code, **not** from
stored dataset metadata. Re-rendering uses whichever config is selected at
runtime:

- default: `CAM_CONFIGS`
- with `--use_cotraining_cameras`: `COTRAIN_CAM_CONFIGS`

### Cotraining camera differences

`COTRAIN_CAM_CONFIGS` uses:
- Wider FOV (65° vs 60°) for agentview cameras
- Different wrist camera pose and intrinsics
- Tighter randomization ranges

If you need to toggle between configs programmatically, set
`use_cotraining_cameras=True` in the environment kwargs, or pass
`--use_cotraining_cameras` to the dataset re-render scripts.

## Preview without full export

To quickly check how camera changes look, use the playback script (it creates
a fresh environment with current `camera_utils.py`):

```bash
python robocasa/scripts/dataset_scripts/playback_dataset.py \
    --dataset /path/to/lerobot --n 1 \
    --render_image_names robot0_agentview_left
```

## Utilities

| Script | Purpose |
|--------|---------|
| `lerobot_extras_to_hdf5.py` | **NEW**: Reconstruct raw HDF5 from LeRobot extras |
| `dataset_states_to_obs.py` | Render image observations from raw HDF5 states (multi-process) |
| `convert_hdf5_lerobot.py` | Re-render + convert raw HDF5 to LeRobot format |
| `playback_dataset.py` | Visualize a LeRobot dataset |
| `playback_dataset_hdf5.py` | Visualize a raw HDF5 dataset |
| `get_dataset_info.py` | Print dataset statistics and filter keys |
| `generate_usd_trajectories.py` | Export trajectories to USD format |
