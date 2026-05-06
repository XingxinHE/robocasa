"""
Script to reconstruct a raw HDF5 dataset from a LeRobot dataset's extras directory.

Use this when you need to re-render camera observations (e.g., with modified camera
extrinsics in camera_utils.py) without re-collecting demonstrations. The output HDF5
is compatible with ``convert_hdf5_lerobot.py`` and ``dataset_states_to_obs.py``.

Usage::

    python robocasa/scripts/dataset_scripts/lerobot_extras_to_hdf5.py \\
        --dataset /path/to/datasets/PickPlaceCounterToCabinet/target/lerobot

    # Specify custom output path
    python robocasa/scripts/dataset_scripts/lerobot_extras_to_hdf5.py \\
        --dataset /path/to/lerobot --output /tmp/reconstructed.hdf5
"""

import argparse
import json
import os
from pathlib import Path

import h5py
import numpy as np
from tqdm import tqdm

import robocasa.utils.lerobot_utils as LU


def build_raw_hdf5(dataset_dir: Path, output_path: str) -> str:
    """
    Reads a LeRobot dataset directory and rebuilds a raw HDF5 file containing
    only states, actions, and metadata (no image observations).

    Returns the path to the generated HDF5.
    """
    dataset_dir = dataset_dir.resolve()

    # --- Read dataset-level metadata ---
    dataset_meta_path = dataset_dir / "extras" / "dataset_meta.json"
    if not dataset_meta_path.exists():
        raise FileNotFoundError(
            f"dataset_meta.json not found at {dataset_meta_path}. "
            "Make sure you are pointing to a valid LeRobot dataset with extras/ present."
        )

    with open(dataset_meta_path) as f:
        dataset_meta = json.load(f)

    env_args = dataset_meta.get("env_args")
    if env_args is None:
        raise KeyError("dataset_meta.json missing 'env_args' key")

    # --- Discover episodes ---
    episode_dirs = LU.get_episodes(dataset_dir)
    if not episode_dirs:
        raise RuntimeError(
            f"No episode_* directories found under {dataset_dir / 'extras'}"
        )

    num_episodes = len(episode_dirs)
    print(f"Found {num_episodes} episodes in {dataset_dir}")

    # --- Write HDF5 ---
    print(f"Writing reconstructed HDF5 to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    total_samples = 0

    with h5py.File(output_path, "w") as f_out:
        data_grp = f_out.create_group("data")

        for ep_idx in tqdm(range(num_episodes), desc="Reconstructing"):
            # Read per-episode data from LeRobot extras
            states: np.ndarray = LU.get_episode_states(dataset_dir, ep_idx)
            model_xml: str = LU.get_episode_model_xml(dataset_dir, ep_idx)
            ep_meta: dict = LU.get_episode_meta(dataset_dir, ep_idx)

            # Read actions from parquet and reorder back to HDF5 format
            actions: np.ndarray = LU.get_episode_actions(dataset_dir, ep_idx)

            num_samples = states.shape[0]
            total_samples += num_samples

            demo_key = f"demo_{ep_idx}"
            demo_grp = data_grp.create_group(demo_key)

            demo_grp.create_dataset("states", data=states)
            demo_grp.create_dataset("actions", data=actions)

            demo_grp.attrs["model_file"] = model_xml
            demo_grp.attrs["ep_meta"] = json.dumps(ep_meta)
            demo_grp.attrs["num_samples"] = num_samples

        # Write dataset-level attributes
        # env_args stored in dataset_meta is already a decoded dict; re-serialize
        data_grp.attrs["env_args"] = json.dumps(env_args)
        data_grp.attrs["total"] = total_samples

    print(f"Done. {num_episodes} episodes, {total_samples} total samples.")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconstruct raw HDF5 from a LeRobot dataset's extras directory."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to the LeRobot dataset directory (the one containing extras/ and data/).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Path for the output HDF5. Defaults to <dataset_parent>/reconstructed.hdf5"
        ),
    )
    args = parser.parse_args()

    dataset_dir = Path(args.dataset)
    if not dataset_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {dataset_dir}")

    output_path = args.output
    if output_path is None:
        output_path = str(dataset_dir.parent / "reconstructed.hdf5")

    build_raw_hdf5(dataset_dir, output_path)


if __name__ == "__main__":
    main()
