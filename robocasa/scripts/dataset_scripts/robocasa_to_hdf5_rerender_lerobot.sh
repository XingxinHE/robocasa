set -euo pipefail
TASKS=(
  /data/robocasa/dataset/v1.0/pretrain/atomic/OpenBlenderLid
  /data/robocasa/dataset/v1.0/pretrain/atomic/PickPlaceCounterToBlender
  /data/robocasa/dataset/v1.0/pretrain/atomic/TurnOnBlender
  /data/robocasa/dataset/v1.0/pretrain/atomic/CloseBlenderLid
  /data/robocasa/dataset/v1.0/target/atomic/CloseBlenderLid
)
for ds in "${TASKS[@]}"; do
  out="$ds/20260504_256x256"
  mkdir -p "$out"
  echo "RECONSTRUCT $ds"
  uv run --group robocasa python third_party/robocasa/robocasa/scripts/dataset_scripts/lerobot_extras_to_hdf5.py \
    --dataset "$ds/20250822/lerobot" \
    --output "$out/reconstructed.hdf5" \
    > "$out/reconstruct.log" 2>&1
  echo "RERENDER $ds"
  uv run --group robocasa python third_party/robocasa/robocasa/scripts/dataset_scripts/convert_hdf5_lerobot.py \
    --raw_dataset_path "$out/reconstructed.hdf5" \
    --camera_names robot0_agentview_left robot0_agentview_right robot0_eye_in_hand \
    --camera_height 256 --camera_width 256 \
    --use_cotraining_cameras \
    > "$out/rerender.log" 2>&1
  echo "DONE $ds"
done
