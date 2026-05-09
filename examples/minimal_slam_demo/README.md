# 最小可运行 SLAM Demo

这里放的是 Git 跟踪的小型示例数据，用于仓库 smoke demo。它不是 TorWIC 原始数据，而是一个手写的轻量对象观测 fixture，用来模拟论文的核心数据模型：

```text
ObjectObservation -> cross-session cluster -> stable MapObject or rejection
```

从仓库根目录运行：

```bash
python tools/run_minimal_demo.py
```

或：

```bash
make demo
```

预期输出：

- `outputs/minimal_demo/summary.json`：机器可读统计；
- `outputs/minimal_demo/map_objects.json`：被保留的稳定语义地标；
- `outputs/minimal_demo/rejected_clusters.json`：被拒绝的动态/瞬时证据；
- `outputs/minimal_demo/report.md`：中文可读报告；
- `outputs/minimal_demo/result.svg`：结果图。

这个 demo 只使用 Python 标准库，不需要 GPU、模型权重、TorWIC 下载或网络。

预期结果图：

![最小 demo 预期结果](expected_result.svg)
