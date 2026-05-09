# 语义分割输出示例

这个目录保存两组真实工业场景中的语义分割输出样例。它们来自本地 TorWIC
pipeline 的已有结果，用于让读者直接看到项目会产生什么样的视觉输出。

## 文件

| 文件 | 含义 |
|---|---|
| `semantic-segmentation-result.png` | 两个实例的总览图：带 bbox/中心点/标签的 overlay、彩色 mask、summary JSON 和地图准入结果 |
| `yellow-barrier-annotated.png` | yellow barrier 的带 bbox、中心点、标签和准入解释的 overlay |
| `yellow-barrier-overlay.png` | yellow barrier 的 overlay 输出 |
| `yellow-barrier-mask.png` | yellow barrier 的二值 mask |
| `yellow-barrier-summary.json` | yellow barrier 的实例摘要 |
| `forklift-annotated.png` | forklift 的带 bbox、中心点、标签和拒绝解释的 overlay |
| `forklift-overlay.png` | forklift 的 overlay 输出 |
| `forklift-mask.png` | forklift 的二值 mask |
| `forklift-summary.json` | forklift 的实例摘要 |
| `tools/build_semantic_example_panel.py` | 重新生成本目录标注图的脚本 |

## 重新生成标注图

在仓库根目录运行：

```bash
make semantic-example
```

等价命令：

```bash
python tools/build_semantic_example_panel.py
```

已验证运行结果：命令会重新生成
`semantic-segmentation-result.png`、`yellow-barrier-annotated.png` 和
`forklift-annotated.png`。标注框和中心点来自 `*-summary.json` 中的
`bbox_min_xyz_m`、`bbox_max_xyz_m` 和 `centroid_xyz_m`，不是手工随意贴上去的。

## 解释

- `yellow_barrier` 是稳定基础设施候选，后续会进入跨会话稳定对象准入判断。
- `forklift` 是动态污染候选，后续地图维护中应被拒绝为动态证据。

这组图不是抽象示意图，而是实际分割输出样例。完整 Grounding DINO/SAM2/OpenCLIP
路径需要本地数据和模型权重；根目录的 `make demo` 则提供无依赖的最小运行闭环。
