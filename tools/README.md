## SAM 2 toolkits

This directory provides toolkits for additional SAM 2 use cases.

### Minimal semantic-SLAM smoke demo

The `run_minimal_demo.py` script is the fastest repository sanity check. It uses
the tiny Git-tracked fixture under `examples/minimal_slam_demo/` and exercises
the paper's core map-admission loop without GPU, model weights, TorWIC downloads,
or network access.

```bash
python ./tools/run_minimal_demo.py
```

Outputs are written to `outputs/minimal_demo/`:

- `summary.json`
- `map_objects.json`
- `rejected_clusters.json`
- `report.md`

### Local Grounded-SAM2 to ObjectObservation bridge

The `demo_local_grounded_sam2_observations.py` script runs the original single-image
`Grounding DINO + SAM2` path on a local RGB image, writes a minimal
`all_instances_manifest.json`, and then builds `ObjectObservation` JSON files for the
paper-v1 pipeline.

It auto-resolves the local cached `grounding-dino-tiny` Hugging Face snapshot and the
first matching SAM2 checkpoint/config pair found in this repo.

```bash
python ./tools/demo_local_grounded_sam2_observations.py \
  --rgb ./notebooks/images/truck.jpg \
  --prompt "car. tire." \
  --output-dir ./outputs/local_grounded_sam2_observation_demo \
  --session-id truck_demo
```

### Semi-supervised VOS inference

The `vos_inference.py` script can be used to generate predictions for semi-supervised video object segmentation (VOS) evaluation on datasets such as [DAVIS](https://davischallenge.org/index.html), [MOSE](https://henghuiding.github.io/MOSE/) or the SA-V dataset.

After installing SAM 2 and its dependencies, it can be used as follows ([DAVIS 2017 dataset](https://davischallenge.org/davis2017/code.html) as an example). This script saves the prediction PNG files to the `--output_mask_dir`.
```bash
python ./tools/vos_inference.py \
  --sam2_cfg configs/sam2.1/sam2.1_hiera_b+.yaml \
  --sam2_checkpoint ./checkpoints/sam2.1_hiera_base_plus.pt \
  --base_video_dir /path-to-davis-2017/JPEGImages/480p \
  --input_mask_dir /path-to-davis-2017/Annotations/480p \
  --video_list_file /path-to-davis-2017/ImageSets/2017/val.txt \
  --output_mask_dir ./outputs/davis_2017_pred_pngs
```
(replace `/path-to-davis-2017` with the path to DAVIS 2017 dataset)

To evaluate on the SA-V dataset with per-object PNG files for the object masks, we need to **add the `--per_obj_png_file` flag** as follows (using SA-V val as an example). This script will also save per-object PNG files for the output masks under the `--per_obj_png_file` flag.
```bash
python ./tools/vos_inference.py \
  --sam2_cfg configs/sam2.1/sam2.1_hiera_b+.yaml \
  --sam2_checkpoint ./checkpoints/sam2.1_hiera_base_plus.pt \
  --base_video_dir /path-to-sav-val/JPEGImages_24fps \
  --input_mask_dir /path-to-sav-val/Annotations_6fps \
  --video_list_file /path-to-sav-val/sav_val.txt \
  --per_obj_png_file \
  --output_mask_dir ./outputs/sav_val_pred_pngs
```
(replace `/path-to-sav-val` with the path to SA-V val)

Then, we can use the evaluation tools or servers for each dataset to get the performance of the prediction PNG files above.

Note: by default, the `vos_inference.py` script above assumes that all objects to track already appear on frame 0 in each video (as is the case in DAVIS, MOSE or SA-V). **For VOS datasets that don't have all objects to track appearing in the first frame (such as LVOS or YouTube-VOS), please add the `--track_object_appearing_later_in_video` flag when using `vos_inference.py`**.
