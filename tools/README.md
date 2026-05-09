## SAM 2 工具

本目录包含仓库中的运行工具、协议工具和 SAM 2 相关工具。

### 最小语义 SLAM smoke demo

`run_minimal_demo.py` 是最快的仓库运行检查入口。它使用
`examples/minimal_slam_demo/` 下的 Git 跟踪小样例数据，不需要 GPU、模型权重、
TorWIC 下载或网络访问，就能跑通论文核心的地图准入闭环。

```bash
python ./tools/run_minimal_demo.py
```

输出写入 `outputs/minimal_demo/`：

- `summary.json`
- `map_objects.json`
- `rejected_clusters.json`
- `report.md`
- `result.svg`

### 本地 Grounded-SAM2 到 ObjectObservation 桥接

`demo_local_grounded_sam2_observations.py` 在本地 RGB 图像上运行原始单图
`Grounding DINO + SAM2` 路径，写出最小 `all_instances_manifest.json`，然后为
paper-v1 管线构建 `ObjectObservation` JSON 文件。

It auto-resolves the local cached `grounding-dino-tiny` Hugging Face snapshot and the
first matching SAM2 checkpoint/config pair found in this repo.

```bash
python ./tools/demo_local_grounded_sam2_observations.py \
  --rgb ./notebooks/images/truck.jpg \
  --prompt "car. tire." \
  --output-dir ./outputs/local_grounded_sam2_observation_demo \
  --session-id truck_demo
```

### 动态 mask 到 SLAM 前端输入

`build_dynamic_slam_frontend_demo.py` 把语义分割输出中的动态实例 mask 转成
SLAM 前端可消费的 masked RGB 和 manifest。这是从“动态物体识别”走向“动态
SLAM 后端评估”的中间桥接层。

```bash
python ./tools/build_dynamic_slam_frontend_demo.py
```

等价入口：

```bash
make dynamic-slam-frontend
```

输出写入 `examples/dynamic_slam_frontend_example/`：

- `dynamic_mask.png`
- `slam_input_masked.png`
- `slam_frontend_manifest.json`
- `dynamic_slam_frontend_result.png`

当前边界：该脚本生成后端输入，不报告 ATE/RPE。

### 动态 SLAM 后端输入包

`build_dynamic_slam_backend_input_pack.py` 在不运行大规模轨迹实验的前提下，
为后端评估准备最小输入包：raw RGB 序列、masked RGB 序列、TUM-style
ground truth 片段和 manifest。

```bash
python ./tools/build_dynamic_slam_backend_input_pack.py
```

等价入口：

```bash
make dynamic-slam-backend-pack
```

输出写入 `outputs/dynamic_slam_backend_input_pack/`：

- `raw/rgb.txt`
- `masked/rgb.txt`
- `groundtruth.txt`
- `backend_input_manifest.json`
- `raw/image_left/*.png`
- `masked/image_left/*.png`
- `masked/dynamic_masks/*.png`

当前边界：该脚本只准备 raw-vs-masked 后端输入和 GT 片段，不调用
DROID-SLAM / ORB-SLAM，也不报告 ATE/RPE。

### 动态 SLAM 后端环境复查与 smoke run

`check_dynamic_slam_backend_env.py` 复查本机统一研究环境 `tram` 中的
PyTorch CUDA、cuDNN、DROID-SLAM、`lietorch`、`evo`、DROID 权重和后端输入包。

```bash
make dynamic-slam-backend-env-check
```

`run_dynamic_slam_backend_smoke.py` 在已有 raw/masked 输入包上运行 bounded
DROID-SLAM smoke，并输出 raw/masked TUM 轨迹估计和 manifest。

```bash
make dynamic-slam-backend-smoke
```

当前边界：8 帧 smoke 只证明 raw-vs-masked 后端和 evo ATE/RPE 路径可执行。
它不是 full-trajectory benchmark，不能证明 masked input 改善建图或导航。

`build_dynamic_slam_backend_input_pack.py --dynamic-mask-summary-dir ...` 可以
把已有语义 frontend 产物中的 forklift masks 按 `rgb_path` 合并到后端输入包，
用于测试真实语义输出覆盖率是否足以影响 DROID-SLAM 轨迹。

```bash
make dynamic-slam-backend-semantic-masks
make dynamic-mask-coverage-figure
```

当前边界：该入口使用已有语义输出，不重新下载模型或重新跑 Grounding DINO/SAM2。
如果 mask 只覆盖少数帧，ATE/RPE 不变化本身就是有效诊断结果。

`evaluate_dynamic_slam_metrics.py` 统一用 evo 复算 raw-vs-masked APE/RPE，并写出
JSON/Markdown 指标文件，避免论文结果靠手工抄表。

`build_dynamic_slam_backend_input_pack.py --temporal-propagation-radius ...`
支持把已有语义 mask 传播到邻近帧，用于诊断“提高时序覆盖后，后端指标是否变得
敏感”。该模式必须作为 stress test 解读，不是真实检测输出。

```bash
make dynamic-slam-backend-temporal-mask-stress
make dynamic-temporal-mask-stress-figure
```

当前边界：P136 传播实验把覆盖提高到 16/64 帧，但 APE/RPE 仍基本持平；
下一步应接入逐帧动态 mask 生成、光流传播或视频分割跟踪。

光流传播压力测试入口：

```bash
make dynamic-slam-backend-flow-mask-stress
make dynamic-flow-mask-stress-figure
```

当前边界：P137 使用稠密光流 warp 同一批已有 masks，结果仍与最近帧传播基本一致。
这说明低成本传播不足以支撑 masked-input gain claim，后续应优先生成真实逐帧
动态 masks。

已有真实逐帧 frontend mask 的后端诊断入口：

```bash
make dynamic-slam-backend-first8-real-masks
make dynamic-first8-real-mask-figure
```

当前边界：P138 使用 `000000` 到 `000007` 八帧已有真实 forklift masks，
不是传播结果。它仍不支持轨迹收益主张，但为下一步“更长窗口真实语义推理”
提供了更干净的基线。

P139 将真实 frontend 推进到 `000000` 到 `000015` 十六帧：

```bash
make dynamic-slam-backend-first16-real-masks
make dynamic-first16-real-mask-figure
```

当前边界：该入口假定 `000008` 到 `000015` 的 frontend 输出已经由
`demo_local_grounded_sam2_observations.py` 生成。若需要重跑 frontend，请使用
`tram` 环境、`PYTHONPATH=/home/rui/slam`、`transformers==4.46.3`、
`checkpoints/sam2_hiera_small.pt` 和 `configs/sam2/sam2_hiera_s.yaml`。

### 半监督 VOS 推理

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
