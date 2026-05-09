# 动态工业环境语义分割辅助 SLAM

本仓库用于推进一篇关于 **动态工业环境中语义分割辅助 SLAM** 的论文和最小可运行系统。

核心思想很简单：开放词汇语义分割产生的对象不能直接写入长期 SLAM 地图。它们应先成为可审计的对象观测，再经过跨会话稳定性、持久性和动态性过滤，最后才决定是进入稳定语义地图，还是作为动态/瞬时证据被拒绝。

## 1. 最小可运行 Demo

这是给外部读者的第一入口。它不需要下载 TorWIC，不加载 Grounding DINO/SAM2/OpenCLIP，不需要 GPU，不访问网络，只使用 Python 标准库和仓库内置的小样例数据。

### 测试环境安装

最低环境：

- Python 3.10 或更高版本；
- Linux/macOS/Windows 均可；
- 不需要 CUDA；
- 不需要模型权重；
- 不需要完整数据集。

建议命令：

```bash
git clone git@github.com:ruirui688/SLAM.git
cd SLAM
python --version
```

可选虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
```

这个最小 demo 没有第三方依赖，所以不需要 `pip install`。

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
| [`tools/run_minimal_demo.py`](./tools/run_minimal_demo.py) | 最小 demo 入口 |
| [`paper/`](./paper/) | 中英文论文稿 |
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
