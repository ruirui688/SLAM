# 动态工业语义分割辅助 SLAM

本仓库服务于一个动态工业场景 SLAM 研究项目，重点是语义前端掩码和长期对象地图维护。核心问题不是“检测器能否在单帧中分割出一个物体”，而是“在叉车、手推车、货物、人员、货架、护栏和工作台共存的仓库中，哪些语义证据应该影响 SLAM 前端，或进入长期对象地图”。

当前项目有两条必须分开的研究线：

- **当前有效路线：** 使用 TorWIC/AnnotatedSemanticSet 数据集自带掩码监督动态/非静态前端掩码训练，然后做有边界的特征级和 SLAM 前端检查。
- **仍然阻塞的路线：** 学习式长期地图准入控制。该路线仍然阻塞，因为缺少独立的 `human_admit_label` 和 `human_same_object_label` 监督。

详细阶段历史见 [RESEARCH_PROGRESS.md](RESEARCH_PROGRESS.md)。最近同步摘要见 [paper/export/latest_progress_summary_p221.md](paper/export/latest_progress_summary_p221.md)。

## 当前科学边界

目前可以安全表述的结论：

- TorWIC/AnnotatedSemanticSet 数据集提供的语义/索引掩码可以监督一个紧凑的二值动态/非静态掩码前端。
- P218 掩码在留出数据上有可测的分割质量，并在一个小型留出包中抑制了真实动态区域内的 ORB 特征点。
- 对象地图维护层目前仍是可审计的规则式准入系统，用于保留稳定对象并拒绝动态污染。

目前**不能**支持的结论：

- 学习式长期地图准入控制。
- 学习式跨会话同一对象关联。
- 将 P193 弱标签准入训练作为可声明的准入监督。
- P218 掩码可带来 raw-vs-masked SLAM 轨迹改进。
- 从六帧 P219/P220 前端掩码包得出 ATE/RPE、地图质量或导航收益结论。

决定准入控制路线是否解锁的门槛是 P195：

- `human_admit_label`：`0/32` 有效标签。
- `human_same_object_label`：`0/160` 有效标签。
- 状态：`BLOCKED`。

## 关键结果

### 动态掩码数据集与训练

P217 从 TorWIC/AnnotatedSemanticSet 数据集提供的语义/索引掩码构建了不需要人工标注的动态/非静态掩码数据集：

| 数量 | 值 |
|---|---:|
| 行数 | 237 |
| 帧组 | 79 |
| 训练 / 验证 / 测试行数 | 156 / 51 / 30 |
| 划分间帧重叠 | 0 |
| 总体正像素率 | 0.374176 |

P218 在 `tram` CUDA 环境和 NVIDIA RTX 3060 上训练了一个紧凑的 UNet 风格二值动态掩码模型：

| 划分 | IoU | F1 | Precision | Recall |
|---|---:|---:|---:|---:|
| Validation | 0.671304 | 0.803329 | 0.716614 | 0.913920 |
| Test | 0.578580 | 0.733038 | 0.601953 | 0.937109 |

训练配置：resize `320x180`，5 epochs，batch size 8，`BCEWithLogitsLoss(pos_weight=1.489919) + 0.5 * DiceLoss`，阈值 `0.40` 由验证集 F1 选择。

### 前端掩码评估

P219 打包了六个留出的验证/测试样本，并报告掩码质量代理指标：

| 指标 | Mean |
|---|---:|
| Predicted masked pixel rate | 0.208691 |
| Ground-truth dynamic pixel rate | 0.137248 |
| Precision / recall / F1 / IoU | 0.556007 / 0.789669 / 0.604636 / 0.443210 |

P220 在 `tram` 环境中使用 OpenCV 审计 ORB 特征级影响：

| 数量 | 值 |
|---|---:|
| Raw ORB keypoints | 10059 |
| Masked ORB keypoints | 9972 |
| Raw keypoints in GT dynamic regions | 4795 |
| Masked keypoints in GT dynamic regions | 2192 |
| GT dynamic-region keypoint reduction | 54.2857% |

P220 有意不报告轨迹 ATE/RPE。P219 包只有六个留出帧，不是带时间戳、标定和对齐轨迹真值的 SLAM 序列。

## 仓库结构

```text
README.md                         面向项目协作者的总览和用法
RESEARCH_PROGRESS.md              分阶段研究日志
tools/                            可复现实验、训练和审计脚本
paper/evidence/                   已跟踪的 JSON/CSV 证据摘要
paper/export/                     可放入论文或汇报的 Markdown 摘要
paper/manuscript_en.md            当前英文论文草稿
paper/tro_submission/             IEEE/T-RO LaTeX 投稿框架
examples/                         最小演示和可视化示例
outputs/                          被 Git 忽略的生成输出、掩码和 checkpoint
```

原始数据、派生图像、模型 checkpoint 和大型生成输出不进入 Git。仓库中跟踪的证据文件用于概括可复现状态。

## 环境

### 最小演示

最小对象地图演示只使用 Python 标准库，不需要 CUDA、PyTorch、模型权重、TorWIC 数据或网络访问。

```bash
python --version
python tools/run_minimal_demo.py
# or
make demo
```

输出写入 `outputs/minimal_demo/`。

### 研究 / CUDA 环境

已记录的本地研究环境是现有 conda 环境 `tram`：

```bash
LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH \
  conda run -n tram <command>
```

已记录的 P218/P220 运行环境：

- NVIDIA GeForce RTX 3060。
- PyTorch `2.4.0+cu118`。
- CUDA/cuDNN 通过 `tram` 可用。
- `tram` 中有 OpenCV，可用于 ORB 代理检查。
- 默认 Python OpenCV 在本机可能因为 NumPy ABI 不匹配而失败；依赖 OpenCV 的检查应使用 `tram`。

新研究机器的一般依赖形态：

```bash
conda create -n slam-research python=3.10 -y
conda activate slam-research
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install evo opencv-python pillow numpy scipy matplotlib tqdm pyyaml
```

除非实验协议明确要求并记录来源/版本，否则不要下载数据或模型权重。

## 可复现命令

以下命令使用已有本地数据重建或检查已跟踪证据；它们不需要创建标签。

```bash
# P195 independent supervision gate; expected status is BLOCKED.
python3 tools/prepare_independent_supervision_p195.py

# P217 dataset manifest from dataset-provided masks.
python3 tools/build_dynamic_mask_dataset_p217.py

# P218 training command used for the recorded CUDA smoke.
LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH \
  /home/rui/miniconda3/bin/conda run -n tram \
  python tools/train_dynamic_mask_p218.py \
    --epochs 5 --batch-size 8 --resize-width 320 --resize-height 180

# P219 held-out front-end masking package.
python3 tools/prepare_frontend_masking_eval_p219.py

# P220 feature-level masking audit; use tram because OpenCV works there.
LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH \
  /home/rui/miniconda3/bin/conda run -n tram \
  python tools/audit_frontend_masking_slam_p220.py
```

只做文档工作时，优先阅读已跟踪报告：

- [paper/export/dynamic_mask_dataset_p217.md](paper/export/dynamic_mask_dataset_p217.md)
- [paper/export/dynamic_mask_training_p218.md](paper/export/dynamic_mask_training_p218.md)
- [paper/export/frontend_masking_eval_p219.md](paper/export/frontend_masking_eval_p219.md)
- [paper/export/frontend_masking_slam_smoke_p220.md](paper/export/frontend_masking_slam_smoke_p220.md)
- [paper/export/independent_supervision_gate_p195.md](paper/export/independent_supervision_gate_p195.md)

## 数据布局

动态掩码训练路线读取本地 TorWIC/AnnotatedSemanticSet 资产：

- `source_image.png`
- `combined_indexedImage.png`
- `raw_labels_2d.json`

P217 在被忽略的 `outputs/dynamic_mask_dataset_p217/` 下派生 RGB 副本和二值动态/非静态掩码，并在 `paper/evidence/` 下写入已跟踪清单。

正掩码类别是：

```text
cart_pallet_jack
fork_truck
goods_material
misc_dynamic_feature
misc_non_static_feature
person
pylon_cone
```

这些是前端动态/非静态掩码目标，**不是**长期地图准入标签。

## 当前阻塞与下一步

- P195 仍然阻塞，直到通过现有协议收集或导入独立的人类准入标签和同一对象标签。
- P219/P220 不能支持轨迹结论，因为当前包缺少带时间戳的图像序列、标定和对齐轨迹真值。
- 下一个有效实验应先从已有本地数据构建时间对齐的留出 raw-vs-P218-masked 序列包，再运行 ORB-SLAM3 或 DROID-SLAM 轨迹评估。
- 任何未来 ATE/RPE 结果都必须先报告轨迹可用性和对齐有效性。

包括早期 DROID/ORB smoke 结果和证据治理工件在内的历史阶段细节，仍保留在 [RESEARCH_PROGRESS.md](RESEARCH_PROGRESS.md) 和 `paper/export/` 中。
