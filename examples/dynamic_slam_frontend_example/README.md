# 动态 mask 到 SLAM 前端输入示例

这个目录展示当前项目向“动态 SLAM 后端闭环”推进的一步：把语义分割得到的动态物体 mask 应用到 RGB 输入帧上，生成后端可消费的 masked RGB 和 manifest。

重新生成：

```bash
make dynamic-slam-frontend
```

输出文件：

| 文件 | 含义 |
|---|---|
| `dynamic_slam_frontend_result.png` | 可视化总览：原始帧、动态 mask、屏蔽后的 SLAM 输入 |
| `dynamic_mask.png` | 动态实例合成 mask，目前示例为 `forklift` |
| `slam_input_masked.png` | 给视觉 SLAM 前端使用的动态区域屏蔽 RGB |
| `slam_frontend_manifest.json` | 后端输入清单、动态实例、coverage 和下一步说明 |

当前边界：

- 已完成：语义分割 mask 到 SLAM 前端输入的文件级桥接；
- 未完成：把这些 masked RGB 帧送入 DROID-SLAM / ORB-SLAM 等后端并报告 ATE/RPE、建图质量或导航收益。
