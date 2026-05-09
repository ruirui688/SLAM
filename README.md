# 动态工业环境语义分割辅助 SLAM

本仓库用于推进一篇关于 **动态工业环境中语义分割辅助 SLAM** 的论文和最小可运行系统。

核心思想很简单：开放词汇语义分割产生的对象不能直接写入长期 SLAM 地图。它们应先成为可审计的对象观测，再经过跨会话稳定性、持久性和动态性过滤，最后才决定是进入稳定语义地图，还是作为动态/瞬时证据被拒绝。

当前工程状态需要明确区分：

- 已打通：语义分割实例输出 -> `ObjectObservation` -> 跨会话对象聚类 -> 稳定对象保留 / 动态污染拒绝；
- 已有可视化：工业场景 overlay、mask、bbox、中心点、summary JSON 和地图准入决策；
- 新增前端桥接：动态 mask -> masked RGB SLAM 输入 -> `slam_frontend_manifest.json`；
- 新增后端输入包：raw RGB / masked RGB / TUM-style GT 片段 -> `backend_input_manifest.json`；
- 新增后端 smoke：DROID-SLAM raw vs masked 8 帧短窗口已生成估计轨迹，并用 evo 报告最小 ATE/RPE；
- 尚未完成：扩大到完整视觉 SLAM 后端轨迹实验，并报告有统计意义的 ATE/RPE、建图质量或导航收益；
- 因此本文当前主张是“语义分割辅助的动态对象过滤与长期对象地图维护”，不是“完整动态 SLAM benchmark 已经闭环优于现有后端”。

## 0. 环境与安装

环境的作用只是隔离依赖和固定运行口径，不是项目能力本身。

本仓库保留两个入口层级：

- **最小 demo 入口**：只使用 Python 标准库，不需要 GPU、CUDA、PyTorch、模型权重或 TorWIC 原始数据；任意 Python 3.10+ 环境都能运行。
- **完整研究/GPU 入口**：用于语义分割、DROID-SLAM、PyTorch CUDA、cuDNN、evo 和 raw-vs-masked 后端实验，需要 GPU 环境、SLAM 后端、模型权重和数据路径。

### 0.1 最小测试环境

适合外部读者快速验证仓库核心对象地图准入闭环。

```bash
git clone git@github.com:ruirui688/SLAM.git
cd SLAM
python --version

# 可选：隔离最小 demo 环境
python -m venv .venv
source .venv/bin/activate

python tools/run_minimal_demo.py
# 或
make demo
```

最低要求：

- Python 3.10 或更高版本；
- Linux/macOS/Windows 均可；
- 不需要 `pip install`；
- 不需要 CUDA、PyTorch、模型权重、TorWIC 原始数据或网络。

### 0.2 完整研究/GPU 环境

适合复现语义分割、动态 mask、DROID-SLAM 后端和 ATE/RPE 评估。推荐使用
conda/mamba 管理，避免系统 Python、`.venv` 和研究依赖混用。

通用安装轮廓：

```bash
# 1. 创建研究环境
conda create -n slam-research python=3.10 -y
conda activate slam-research

# 2. 安装 CUDA 版 PyTorch；版本需按本机驱动/CUDA 调整
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. 安装评估和常用工具
pip install evo opencv-python pillow numpy scipy matplotlib tqdm pyyaml

# 4. 安装或接入 DROID-SLAM
git clone https://github.com/princeton-vl/DROID-SLAM.git thirdparty/DROID-SLAM
pip install -e thirdparty/DROID-SLAM

# 5. 可选：安装语义前端依赖
# Grounding DINO / SAM2 / OpenCLIP 的权重和版本按实验需要单独固定。
```

完整研究环境还需要：

- NVIDIA GPU 和可用驱动；
- CUDA/cuDNN 与 PyTorch wheel 匹配；
- DROID-SLAM 权重，例如 `droid.pth`；
- TorWIC 或等价 RGB/GT 数据；
- 如需自动语义分割，另需 Grounding DINO、SAM2、OpenCLIP 及对应权重。

网络较慢时可以设置代理或使用镜像，但 PyTorch CUDA wheel、DROID-SLAM、模型权重和数据集应固定版本并记录来源，避免论文结果不可复现。

### 0.3 本机已验证环境

在这台机器上，持续推进研究时统一使用现有 conda 环境 `tram`：

```bash
LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH conda run -n tram <command>
```

后端环境复查入口：

```bash
make dynamic-slam-backend-env-check
```

已验证：`tram` 环境中 PyTorch `2.4.0+cu118`、CUDA、cuDNN、`droid_backends`、`lietorch`、`evo`、DROID-SLAM 权重和后端输入包均可用。沙箱化探测可能看不到 `/dev/nvidia*`，不应据此判断整机 GPU 不可用。

## 1. 最小可运行 Demo

这是给外部读者的第一入口。它不需要下载 TorWIC，不加载 Grounding DINO/SAM2/OpenCLIP，不需要 GPU，不访问网络，只使用 Python 标准库和仓库内置的小样例数据。

测试环境和完整研究环境的安装方法见 §0。这个最小 demo 没有第三方依赖，所以不需要 `pip install`。

### 运行入口

方式一：

```bash
python tools/run_minimal_demo.py
```

方式二：

```bash
make demo
```

它运行的最小闭环是：

```text
ObjectObservation -> cross-session cluster -> retained MapObject or rejection
```

输入样例：

```text
examples/minimal_slam_demo/observations.json
```

输出目录：

```text
outputs/minimal_demo/
```

### 已验证的测试结果

我在本仓库当前环境中运行：

```bash
make demo
```

得到输出：

```json
{
  "input": "/home/rui/slam/examples/minimal_slam_demo/observations.json",
  "output_dir": "/home/rui/slam/outputs/minimal_demo",
  "observations": 11,
  "clusters": 4,
  "retained_stable_map_objects": 2,
  "rejected_clusters": 2,
  "criteria": {
    "min_sessions": 2,
    "min_observations": 3,
    "max_dynamic_ratio": 0.34,
    "min_label_purity": 0.6
  }
}
```

生成文件：

```text
outputs/minimal_demo/summary.json
outputs/minimal_demo/map_objects.json
outputs/minimal_demo/rejected_clusters.json
outputs/minimal_demo/report.md
outputs/minimal_demo/result.svg
```

结果图如下：

![最小 demo 终端运行结果](examples/minimal_slam_demo/terminal_result.svg)

![最小语义 SLAM Demo 结果](examples/minimal_slam_demo/expected_result.svg)

### 语义分割输出示例

上面的最小 demo 证明仓库可以无依赖跑通地图准入闭环。下面这张图展示更接近论文 pipeline 的实际语义分割输出：同一 TorWIC 工业场景中的实例 overlay、二值 mask、summary JSON，以及进入对象地图前的“保留候选 / 动态拒绝”判断。图中的 bbox 和中心点来自实例 summary JSON，不是后期随意贴上去的装饰。

![语义分割实际输出示例](examples/semantic_segmentation_example/semantic-segmentation-result.png)

可以重新生成这张标注图：

```bash
make semantic-example
```

验证输出：

```text
examples/semantic_segmentation_example/semantic-segmentation-result.png
examples/semantic_segmentation_example/yellow-barrier-annotated.png
examples/semantic_segmentation_example/forklift-annotated.png
```

示例文件：

```text
examples/semantic_segmentation_example/semantic-segmentation-result.png
examples/semantic_segmentation_example/yellow-barrier-annotated.png
examples/semantic_segmentation_example/yellow-barrier-overlay.png
examples/semantic_segmentation_example/yellow-barrier-mask.png
examples/semantic_segmentation_example/yellow-barrier-summary.json
examples/semantic_segmentation_example/forklift-annotated.png
examples/semantic_segmentation_example/forklift-overlay.png
examples/semantic_segmentation_example/forklift-mask.png
examples/semantic_segmentation_example/forklift-summary.json
```

解释：

- `yellow_barrier` 是稳定基础设施候选，后续可进入跨会话稳定对象准入判断；
- `forklift` 是动态污染候选，后续地图维护中应被拒绝为动态证据；
- 这组图是实际语义分割输出样例，不是抽象流程图；
- 它展示的是“语义分割实例输出 -> ObjectObservation -> 跨会话聚类 -> 稳定对象保留 / 动态证据拒绝”的论文链路。

### 真实工业场景示例

上面的 SVG 是运行 `make demo` 后的结构化结果图，展示仓库可以实际跑出“保留稳定对象 / 拒绝动态证据”的结果。下面两张图只用于说明项目面向的真实工业场景，不在图上强行标注对象位置，避免误导读者。

**图 1：TorWIC 工业 RGB-D 重访中的分割 overlay。**

这张图展示 TorWIC 工业 RGB-D 重访中的真实场景和 segmentation overlay。它说明项目处理的不是玩具场景，而是真实工业环境中的语义观测。

![TorWIC 工业场景分割 overlay](paper/figures/torwic_real_session_overlays.png)

**图 2：Hallway 更广泛验证分支结果。**

这张图展示 Hallway 10-session broader-validation 分支。它用于展示项目在另一个工业回访场景中的验证材料，不替代最小 demo 的运行结果。

![TorWIC Hallway 更广泛验证 composite](paper/figures/torwic_hallway_composite.png)

结果解释：

- `safety barrier` 和 `warehouse rack` 跨 3 个 session 重复出现，被保留为稳定地图对象；
- `forklift` 虽然跨 session 出现，但动态比例为 1.0，被拒绝为动态污染；
- `pallet stack` 只在单 session 出现，且是瞬时对象，被拒绝；
- 这正对应论文主张：语义分割输出是候选证据，不是可直接写入持久地图的真值。

### 动态 SLAM 前端输入示例

这一步把动态语义 mask 继续往 SLAM 方向推进：将 `forklift` 动态区域从 RGB 输入中屏蔽，生成给 DROID-SLAM / ORB-SLAM 这类视觉前端可消费的 masked RGB 和 manifest。

运行：

```bash
make dynamic-slam-frontend
```

已验证输出：

```text
examples/dynamic_slam_frontend_example/dynamic_mask.png
examples/dynamic_slam_frontend_example/slam_input_masked.png
examples/dynamic_slam_frontend_example/slam_frontend_manifest.json
examples/dynamic_slam_frontend_example/dynamic_slam_frontend_result.png
```

![动态 mask 到 SLAM 前端输入示例](examples/dynamic_slam_frontend_example/dynamic_slam_frontend_result.png)

这还不是完整 ATE/RPE 实验，但已经把“语义分割动态物体”转换成了 SLAM 前端可消费的输入形式。

### 动态 SLAM 后端输入包

继续往后端评估推进一步，可以生成一个 bounded raw-vs-masked 输入包：连续
TorWIC 左目 RGB 小窗口、对应 TUM-style ground truth 片段、raw/masked 两套
`rgb.txt` 和 manifest。

运行：

```bash
make dynamic-slam-backend-pack
```

已验证输出写入 ignored `outputs/`：

```text
outputs/dynamic_slam_backend_input_pack/raw/rgb.txt
outputs/dynamic_slam_backend_input_pack/masked/rgb.txt
outputs/dynamic_slam_backend_input_pack/groundtruth.txt
outputs/dynamic_slam_backend_input_pack/backend_input_manifest.json
```

### 动态 SLAM 后端 smoke 与最小 ATE/RPE

在本机 `tram` conda 环境中，已经完成一个 bounded DROID-SLAM smoke run：

```bash
make dynamic-slam-backend-smoke
```

已验证输出写入 ignored `outputs/`：

```text
outputs/dynamic_slam_backend_smoke_p132/raw_estimate_tum.txt
outputs/dynamic_slam_backend_smoke_p132/masked_estimate_tum.txt
outputs/dynamic_slam_backend_smoke_p132/dynamic_slam_backend_smoke_manifest.json
outputs/dynamic_slam_backend_smoke_p132/p132_p133_raw_vs_masked_metrics.md
```

8 帧 smoke 结果：

| 输入 | APE RMSE (m) | RPE RMSE (m) |
|---|---:|---:|
| raw RGB | 0.001242 | 0.002250 |
| masked RGB | 0.001243 | 0.002255 |

当前边界：这证明 raw-vs-masked 后端运行和 evo ATE/RPE 路径已经打通；但短窗口 raw/masked 基本持平，不能声称 masked input 已改善完整轨迹、建图质量或导航收益。

P134 进一步扩大到 64 帧，并启用 DROID-SLAM global BA：

```bash
make dynamic-slam-backend-64
```

64 帧 global BA 结果：

| 输入 | APE RMSE (m) | RPE RMSE (m) |
|---|---:|---:|
| raw RGB | 0.051135 | 0.032713 |
| masked RGB | 0.051136 | 0.032713 |

![64 帧 DROID-SLAM global BA raw-vs-masked 结果](paper/figures/torwic_dynamic_slam_backend_p134.png)

当前解释：64 帧后端链路已经可执行，raw/masked 仍基本持平；由于当前动态 mask 只作用于第 `000002` 帧，不能据此主张 masked input 带来轨迹收益。

P135 继续推进到已有语义 frontend masks：从
`outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1/frontend_output`
读取真实 forklift mask summary，按 `rgb_path` 合并到 64 帧后端输入包。

```bash
make dynamic-slam-backend-semantic-masks
make dynamic-mask-coverage-figure
```

结果诊断：

| 输入 | APE RMSE (m) | RPE RMSE (m) |
|---|---:|---:|
| raw RGB | 0.051135 | 0.032713 |
| semantic masked RGB | 0.051135 | 0.032713 |

![真实语义 mask 覆盖率诊断](paper/figures/torwic_dynamic_mask_coverage_p135.png)

当前解释：已有真实语义 mask 已接入后端，但只覆盖 64 帧中的 `000004`、`000005`、`000007`，64 帧平均覆盖率约 `0.026%`。这个结果不是失败，而是定位出下一步研究瓶颈：需要跨更多帧生成/传播动态 mask，才有可能观察到动态 masking 对轨迹的影响。

P136 做一个诚实的时序传播压力测试：把已有真实 forklift masks 按最近帧传播到
`±8` 帧，并做 `4 px` 膨胀。它不是新的 detector 输出，而是用来回答一个研究问题：
“如果覆盖率提高，后端指标是否开始对动态 masking 敏感？”

```bash
make dynamic-slam-backend-temporal-mask-stress
make dynamic-temporal-mask-stress-figure
```

结果：

| 输入 | APE RMSE (m) | RPE RMSE (m) |
|---|---:|---:|
| raw RGB | 0.051135 | 0.032713 |
| temporal propagated masked RGB | 0.051222 | 0.032710 |

![时序传播 mask 压力测试](paper/figures/torwic_dynamic_mask_temporal_stress_p136.png)

当前解释：mask 覆盖从 P135 的 `3/64` 帧、均值 `0.025750%` 提高到 `16/64` 帧、均值 `0.267154%`，但 APE/RPE 仍基本持平。这说明简单最近帧传播还不足以形成可靠轨迹收益；下一步应做真正的逐帧动态 mask 生成或基于光流/视频分割的时序跟踪，而不是继续只扩大 SLAM 后端窗口。

## 2. 论文稿件

| 稿件 | 路径 | 用途 |
|---|---|---|
| 英文进度稿 | [`paper/manuscript_en.md`](./paper/manuscript_en.md) | 轻量英文稿 |
| 中文进度稿 | [`paper/manuscript_zh.md`](./paper/manuscript_zh.md) | 轻量中文稿 |
| 英文厚稿 | [`paper/manuscript_en_thick.md`](./paper/manuscript_en_thick.md) | 厚实英文初稿 |
| 中文厚稿 | [`paper/manuscript_zh_thick.md`](./paper/manuscript_zh_thick.md) | 厚实中文初稿 |

当前厚稿已经包含 Related Work、Problem Formulation、Method、Experimental Protocol、Results、Failure-case Analysis、Discussion、Limitations、References、Figure Captions 和 Evidence Ladder Summary。

## 3. 当前证据栈

主线证据是 TorWIC Aisle 重访阶梯：

| 设置 | 会话数 | 帧级对象 | 跨会话聚类 | 保留稳定对象 |
|---|---:|---:|---:|---:|
| Same-day Aisle | 4 | 203 | 11 | 5 |
| Cross-day Aisle | 4 | 240 | 10 | 5 |
| Cross-month Aisle | 6 | 297 | 14 | 7 |

次级广泛验证分支是 TorWIC Hallway：

| 分支 | 会话数 | 执行帧 | 帧级对象 | 跨会话聚类 | 保留稳定对象 |
|---|---:|---:|---:|---:|---:|
| Hallway broader validation | 10 | 80/80 first-eight-frame commands | 537 | 16 | 9 |

解释规则：

- Aisle 是主控证据阶梯；
- Hallway 是次级广泛验证，不并入主 Aisle 阶梯；
- 历史 `172/15/5` cross-month family 只作为 fallback chronology；
- larger-window 或 full-trajectory 实验需要单独批准。

## 4. 仓库结构

| 路径 | 作用 |
|---|---|
| [`examples/minimal_slam_demo/`](./examples/minimal_slam_demo/) | Git 跟踪的最小可运行样例数据 |
| [`examples/dynamic_slam_frontend_example/`](./examples/dynamic_slam_frontend_example/) | 动态 mask 到 SLAM 前端 masked RGB 的最小桥接示例 |
| [`tools/run_minimal_demo.py`](./tools/run_minimal_demo.py) | 最小 demo 入口 |
| [`tools/build_dynamic_slam_backend_input_pack.py`](./tools/build_dynamic_slam_backend_input_pack.py) | raw-vs-masked 后端输入包生成入口 |
| [`tools/check_dynamic_slam_backend_env.py`](./tools/check_dynamic_slam_backend_env.py) | 本机 `tram` GPU/DROID/evo 后端环境复查 |
| [`tools/run_dynamic_slam_backend_smoke.py`](./tools/run_dynamic_slam_backend_smoke.py) | DROID-SLAM raw-vs-masked smoke run |
| [`tools/evaluate_dynamic_slam_metrics.py`](./tools/evaluate_dynamic_slam_metrics.py) | 统一生成 raw-vs-masked evo APE/RPE JSON/Markdown 指标 |
| [`tools/plot_dynamic_mask_coverage_diagnostic.py`](./tools/plot_dynamic_mask_coverage_diagnostic.py) | 生成动态 mask 覆盖率和后端指标论文图 |
| [`paper/`](./paper/) | 中英文论文稿 |
| [`paper/evidence/`](./paper/evidence/) | Git 可见的实验结果证据包，由 `make evidence-pack` 从 ignored `outputs/` 生成 |
| [`RESEARCH_PROGRESS.md`](./RESEARCH_PROGRESS.md) | 研究机器人和论文进度日志 |
| [`DATA_SOURCES.md`](./DATA_SOURCES.md) | 数据来源、下载入口和 Git 排除策略 |
| [`DATA_ORGANIZATION.md`](./DATA_ORGANIZATION.md) | 数据组织和恢复说明 |
| [`config/protocols/`](./config/protocols/) | TorWIC 协议配置 |
| [`tools/`](./tools/) | 数据、协议、对象观测和报告工具 |
| [`sam2/`](./sam2/) | SAM2 相关代码 |
| [`grounding_dino/`](./grounding_dino/) | Grounding DINO 相关代码 |

## 5. 核心流水线

论文中的完整系统围绕如下对象维护链路组织：

```text
RGB-D frames
  -> text-guided detection
  -> SAM2 masks
  -> OpenCLIP label/reranking checks
  -> 2D-to-3D object initialization
  -> ObjectObservation
  -> TrackletRecord
  -> cross-session MapObject
  -> retained stable landmark or rejected transient/dynamic evidence
```

最小 demo 不运行大模型，而是用小型 JSON fixture 直接模拟 `ObjectObservation` 之后的地图准入逻辑，便于快速测试和审阅。

## 6. 数据和 Git 策略

完整数据集：

- TorWIC SLAM Dataset / Toronto Warehouse Incremental Change SLAM Dataset；
- 本地路径：`/home/rui/slam/data/TorWIC_SLAM_Dataset`；
- Git 策略：完整数据不提交；
- 下载和恢复入口见 [`DATA_SOURCES.md`](./DATA_SOURCES.md) 与 [`DATA_ORGANIZATION.md`](./DATA_ORGANIZATION.md)。

不要提交：

- `data/`
- `outputs/`
- `tmp/`
- `checkpoints/`
- `gdino_checkpoints/`
- `.bag`、压缩包、视频、点云、mask、模型权重和大型生成产物。

小型 demo fixture 可以提交；运行生成的 `outputs/minimal_demo/` 不提交。

## 7. 当前状态

截至 2026-05-09：

- 已有厚版中英文论文初稿；
- 已有 P114-P119 证据和投稿包闭环；
- 已有最小可运行 demo；
- 当前没有新数据下载；
- 当前没有新实验 protocol 在运行。

下一步必须是明确方向，例如：目标 venue 格式化、引用后端补强、更丰富可视化 demo、或经批准的更大实验。
