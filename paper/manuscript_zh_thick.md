# 面向动态工业环境的语义分割辅助 SLAM：
# 面向对象地图维护与有界动态掩码前端证据

**厚稿 v2 - 中文**
*更新：2026-05-13 | 厚稿为当前唯一主稿目标 | 仅使用现有证据*

---

## 摘要

工业环境中的长期视觉 SLAM 面临两个相关但不同的动态场景问题。第一，语义地图可能被真实存在、反复检测、但不应进入静态持久地图的物体污染，例如叉车和临时车辆。第二，动态区域中的视觉特征可能影响前端或后端轨迹估计。本文将第一类问题作为主贡献，将第二类问题作为有界前端 smoke 证据。我们提出**会话级地图准入控制**：在开放词汇 RGB-D 感知与持久语义地图之间加入对象维护层，将分割输出整理为 observation、tracklet、map-object 和 revision 记录，再用多会话出现、观测支持、标签一致性、静态占优和帧覆盖等可审计准则决定准入或拒绝。

在 POV-SLAM/TorWIC 工业数据集 [6] 上，对象维护证据链在 Same-day Aisle（203 个观测 / 11 个簇 / 5 个保留）、Cross-day Aisle（240/10/5）、Cross-month Aisle（297/14/7）和独立 Hallway 迁移分支（537/16/9）中稳定保留基础设施对象，并一致拒绝叉车类动态污染。叉车类拒绝占比为 50.0%-71.4%。

本文同时整合后续动态掩码前端证据。P217 数据集包含 237 行，156/51/30 划分，零帧重叠，正像素率 0.374176。P218 compact UNet 的验证 IoU/F1 为 0.671304/0.803329，测试 IoU/F1 为 0.578580/0.733038。P219 held-out precision/recall/F1/IoU 为 0.556007/0.789669/0.604636/0.443210。P220 中 GT 动态区域 ORB 关键点从 4795 降到 2192，减少 54.2857%。P225-P228 构建 60 帧 Oct. 12, 2022 Aisle_CW raw-vs-masked 序列和 confidence/coverage-gated hard black mask module。P228 在原始 480-539 窗口上保持中性：raw/masked APE 0.088496/0.084705，RPE 0.076145/0.076224，ORB gated-region 关键点 8969 -> 5073。但 P233-P234 说明 hard-boundary gate 的跨窗口结果是 mixed：120-179 为 5927 -> 4820，而 840-899 反向变成 601 -> 1901；failure sweep 没有找到稳定的 post-processing-only 设置，最佳仍为 127 -> 1197。P235 因此测试 soft boundary/mean-fill feather candidate `meanfill035_feather5_thr060_cap012_min256`，在有界 smoke 中修复 840-899 回归窗口：ORB 127 -> 0，总关键点 delta 为 0；DROID 16f dAPE -0.000036/dRPE +0.000007，60f dAPE +0.000158/dRPE -0.000003；回测 480-539 为 1382 -> 188，120-179 为 215 -> 20。这些结果只支持有界前端模块候选和失败诊断，不支持 full benchmark、navigation、independent-label 或 learned map-admission 结论。P195 仍为 BLOCKED。

## 关键词

SLAM；语义分割；动态物体过滤；对象级地图；地图维护；工业机器人；开放词汇感知；动态掩码；长期自主

---

## 一、引言

### 一.A. 动机

长期工业 SLAM 的难点已经从单次几何建图转向长期可用地图维护 [1]。仓储环境同时包含稳定基础设施（护栏、工作台、货架、立柱）和动态设备（叉车、推车、人员）。开放词汇感知模型如 Grounding DINO [7]、SAM2 [8] 和 OpenCLIP [9] 可以从 RGB-D 帧中产生大量对象候选，但“被检测到”并不等于“应进入持久地图”。

### 一.B. 准入控制缺口

动态 SLAM 方法如 DynaSLAM [2] 主要通过遮挡动态区域保护轨迹和重建。对象级 SLAM 和开放词汇 3D 建图 [3]-[5] 关注对象语义表示。二者都没有直接解决持久语义地图准入问题：一个被正确检测、甚至反复检测到的叉车，仍然可能是错误的静态地图实体。

### 一.C. 范围与贡献

本文厚稿按两条证据线组织：

1. **主贡献：面向对象地图维护。** 定义 observation、tracklet、map-object 和 revision 记录，使用可解释 trust score 和布尔准入准则，保留稳定基础设施并拒绝动态污染。
2. **辅助证据：有界动态掩码前端。** 整合 P217-P235 的数据集、compact UNet、ORB proxy、60 帧 DROID raw-vs-masked smoke、P228 hard gate、P233-P234 失败诊断和 P235 soft-boundary candidate。该线只支持前端模块故事，不支持完整动态 SLAM 或导航效果声明。

本文不声称解决完整 lifelong SLAM、稠密动态重建、独立动态分割真值、下游导航效果或 learned persistent-map admission。

---

## 二、相关工作

### 二.A. 语义 SLAM 与对象级建图

Cadena 等 [1] 总结了 SLAM 从几何估计到鲁棒感知的发展。CubeSLAM [3] 使用对象级立方体表示支持单目 SLAM。OpenScene [4] 和 ConceptFusion [5] 将开放词汇语义与 3D 表示结合。本文与这些工作互补：我们不主要研究如何检测对象，而是研究检测后哪些对象可以进入长期地图。

### 二.B. 动态 SLAM 与动态物体抑制

DynaSLAM [2] 通过动态区域遮挡提升动态场景中的跟踪和建图鲁棒性。本文采用该方向的动机，但决策层次不同：我们在语义地图层拒绝动态类对象，而不是仅在图像或几何层过滤动态像素。

### 二.C. 长期地图维护

长期 SLAM 需要决定保留、更新、遗忘和修订哪些地图实体 [1]。POV-SLAM/TorWIC [6] 提供了工业重访数据和对象级语义背景。本文将 TorWIC 作为证据来源，用会话级证据聚合做显式准入控制。

### 二.D. 分割辅助和开放词汇前端

Grounding DINO [7]、SAM2 [8] 和 OpenCLIP [9] 在对象维护线中作为黑盒感知前端。动态掩码线进一步使用从语义 mask 派生的数据训练小型动态区域模型。模型本身不是本文主贡献。

---

## 三、问题形式化

给定 SLAM 会话 \(S_k\) 中的 RGB-D 帧 \(F_{k,1}, \ldots, F_{k,N_k}\)，感知前端输出对象观测 \(o_{k,i}^{(j)}\)，每个观测包含 frame id、session id、bbox、mask、canonical label、confidence 和可选状态标签。

**地图准入问题**是构建持久对象地图 \(\mathcal{M}\)，使保留对象满足：

| 要求 | 工业语义 SLAM 含义 |
|---|---|
| 稳定性 | 对象在多次重访中物理持久存在。 |
| 一致性 | 标签和空间支持足够稳定。 |
| 静态占优 | 动态设备和移动代理不进入静态持久地图。 |
| 可审计 | 每个准入/拒绝决策能追溯到观测、会话和准则。 |

动态掩码前端问题是另一条线：学习或门控动态区域 mask，观察其对 raw-vs-masked SLAM 输入和特征区域的影响。当前仅作为有界 smoke，不作为完整 SLAM 改进证明。

---

## 四、系统总览

系统包含两条分离的路径。

### 四.A. 对象维护路径

对象维护路径将开放词汇对象观测转换为 revisioned map objects，负责稳定基础设施保留、动态污染拒绝和逐对象 provenance。该路径是本文主贡献。

### 四.B. 动态掩码前端路径

动态掩码路径训练或应用动态区域 mask，进行后处理、masked RGB 输入或特征区域分析，并报告有界 raw-vs-masked 证据。当前结论是：learned mask 可以抑制预测动态区域中的 ORB 特征，hard black gate 存在边界特征失败模式，而 soft boundary/mean-fill feather candidate 在有界 smoke 中修复了该回归窗口，同时 DROID-SLAM 轨迹 delta 保持中性。

### 四.C. 证据边界

对象维护评估的是地图准入；动态掩码评估的是前端遮挡行为和 bounded backend execution。两条线不能合并成 learned persistent-map admission 结论。

---

## 五、面向对象地图维护

### 五.A. 开放词汇对象观测

每帧 RGB-D 图像通过 Grounding DINO [7] 产生工业类别框，通过 SAM2 [8] 生成实例 mask，通过 OpenCLIP [9] 做标签重排或消歧。每个候选转换为 `ObjectObservation`，记录帧、会话、bbox、mask、多边形、canonical label、confidence、timestamp 和状态元数据。

### 五.B. 会话级 Tracklet

同一会话内，标签和空间支持相容的观测聚合成 tracklet。tracklet 记录 session id、时间范围、观测数、帧数、标签直方图、状态直方图和 dynamic ratio。tracklet 是会话内证据单元，不直接进入持久地图。

### 五.C. 跨会话 MapObject

不同会话的 tracklet 通过 canonical label 和空间 IoU（当前阈值 0.1）合并为 `MapObject`。该记录聚合 session support、total observations、tracklets、dominant label、label purity、dominant state、spatial stability 和逐会话 provenance。

### 五.D. 稳定性与动态性评分

辅助 trust score 为：

\[
\tau(O)=\alpha s_{\text{session}}(O)+\beta s_{\text{support}}(O)-\gamma s_{\text{dynamic}}(O)
\]

当前 \(\alpha=0.4\)、\(\beta=0.3\)、\(\gamma=0.5\)。该分数不是最优估计器，而是可解释诊断；最终准入仍由布尔准则决定。

### 五.E. 地图准入准则

| 准则 | 条件 | 理由 |
|---|---:|---|
| 多会话出现 | sessions >= 2 | 单会话对象可能是临时物。 |
| 最小支持 | observations >= 6 | 低支持对象不可靠。 |
| 标签一致性 | label purity >= 0.70 | 混合标签表示检测歧义。 |
| 静态占优 | dynamic ratio <= 0.20 | 动态代理不进入静态地图。 |
| 最小帧数 | frames >= 4 | 过少帧缺少空间支持。 |

失败对象以 `dynamic_contamination`、`single_session_or_low_session_support`、`label_fragmentation`、`low_support` 等原因记录。

### 五.F. 修订式地图更新

新会话到来时，tracklet 可以确认已有对象、形成新候选，或被拒绝。地图以 revision 方式更新，稳定对象累计证据，失败对象保留拒绝原因。

---

## 六、动态掩码前端

### 六.A. P217-P220 数据与模型

| 证据 | 数值 |
|---|---:|
| P217 rows | 237 |
| P217 split | 156 train / 51 val / 30 test |
| frame overlap | 0 |
| positive pixel rate | 0.374176 |

| 模型证据 | IoU | F1 |
|---|---:|---:|
| P218 validation | 0.671304 | 0.803329 |
| P218 test | 0.578580 | 0.733038 |

P219 held-out precision/recall/F1/IoU 为 0.556007/0.789669/0.604636/0.443210。P220 中 GT dynamic-region ORB 关键点从 4795 降到 2192，减少 54.2857%。这些结果支持 compact dynamic-mask frontend 的可行性，但不构成独立动态分割真值。

### 六.B. P225 学习掩码序列

P225 构建 Oct. 12, 2022 Aisle_CW source indices 480-539 的 60 帧 raw-vs-learned-mask 序列。由于 P218 checkpoint 不可用，P225 使用从 P217 semantic masks 有界重训的 SmallUNet。该包是 trajectory-ready input only，不是轨迹结论。

### 六.C. P227 DROID Baseline

P227 在 P225 序列上复现 DROID-SLAM [10] raw-vs-masked baseline：60 帧 APE 0.088504/0.084529，RPE 0.076145/0.076226；ORB predicted-region 关键点 21030 -> 18617。状态为中性，不是改进声明。

### 六.D. P228-P235 Confidence/Coverage Gate 与 Soft-Boundary Candidate

| 参数 | 数值 |
|---|---:|
| probability threshold | 0.50 |
| dilation | 1 px |
| min component | 128 px |
| max/target coverage | 0.22 / 0.18 |
| mean coverage | 14.127053% |

P228 原始 480-539 窗口 60 帧 raw/masked APE 为 0.088496/0.084705，RPE 为 0.076145/0.076224，ORB gated-region 关键点 8969 -> 5073。相比 P227，P228 轨迹 smoke 仍中性，并给出原始动态掩码前端故事种子。

P233 将同一 hard black gate 扩展到两个不重叠的 Aisle_CW 窗口，结果是 mixed：120-179 轨迹中性且 ORB gated-region 关键点 5927 -> 4820，但 840-899 虽轨迹近中性，ORB proxy 却从 601 反向增到 1901。P234 在 840-899 failure window 上扫描 threshold、coverage、component area 和 dilation，没有任何 post-processing-only hard gate 同时满足 ORB proxy 下降和 DROID 中性；最佳 proxy variant 仍为 127 -> 1197。诊断是 hard black mask 边界会制造 ORB corners，coverage/threshold 调参本身不是稳定修复。

P235 在同一概率图上测试 soft boundary/mean-fill feather frontend。选定候选为 `meanfill035_feather5_thr060_cap012_min256`：mean-fill、feather sigma 5、probability threshold 0.60、max/target coverage 0.12/0.10、minimum component area 256 px。在第一个回归窗口 840-899 上，该候选将 ORB predicted-region 关键点从 127 降到 0，总关键点 delta 为 0。DROID delta 在有界 gate 中保持中性：16-frame dAPE -0.000036、dRPE +0.000007；60-frame dAPE +0.000158、dRPE -0.000003。回测同样是 ORB-positive 且 16-frame trajectory-neutral：480-539 为 1382 -> 188，120-179 为 215 -> 20。

正确解释应保持很窄：hard black confidence/coverage gating 有已记录的 boundary-feature failure mode，P235 soft-boundary candidate 在有界 smoke 中修复了观测到的回归窗口。它不是 full dynamic-SLAM benchmark、navigation gain、independent-label validation 或 learned map-admission result。

---

## 七、实验协议

### 七.A. 对象维护协议

所有对象维护协议使用相同准则：min_sessions=2、min_frames=4、min_support=6、max_dynamic_ratio=0.2、min_label_purity=0.7。没有按协议调参。

| 协议 | 会话 | 观测 | 候选簇 | 保留对象 | 角色 |
|---|---:|---:|---:|---:|---|
| Same-day Aisle | 2022-06-15 三个会话 | 203 | 11 | 5 | 主证据起点 |
| Cross-day Aisle | 2022-06-15 + 2022-06-23 | 240 | 10 | 5 | 8 天重访 |
| Cross-month Aisle | 2022-06 + 2022-10 | 297 | 14 | 7 | 4 个月重访 |
| Hallway | 已执行前 8 个会话 | 537 | 16 | 9 | 次级场景迁移 |

### 七.B. 动态掩码协议

| 阶段 | 协议 | 声明状态 |
|---|---|---|
| P135-P143 | 64 帧 TorWIC Aisle 动态掩码 backend diagnostics | 负结果边界：叉车区域太小，轨迹中性。 |
| P217-P220 | compact dynamic-mask 数据、模型、ORB sanity | 前端可行性。 |
| P225-P228 | 60 帧 Oct. 12, 2022 Aisle_CW learned mask 和 hard confidence/coverage-gated DROID smoke | 原始有界前端故事种子。 |
| P233-P235 | hard-gate multi-window validation、failure sweep 和 soft-boundary candidate | hard gate mixed/failure 证据加有界候选修复；不是完整 benchmark。 |

---

## 八、结果

### 八.A. Aisle 主证据链

| 协议 | 观测 | 簇 | 保留 | 主要保留类别 | 主要拒绝模式 |
|---|---:|---:|---:|---|---|
| Same-day Aisle | 203 | 11 | 5 | 2 工作台、2 货架、1 护栏 | 3 叉车类动态，3 单会话 |
| Cross-day Aisle | 240 | 10 | 5 | 同类稳定对象 | 3 叉车类动态，2 单会话 |
| Cross-month Aisle | 297 | 14 | 7 | 新增护栏/货架达到支持 | 5 叉车类动态，2 单会话 |

### 八.B. 稳定子集构成

| 类别 | Same-day | Cross-day | Cross-month | Hallway |
|---|---:|---:|---:|---:|
| Barrier | 1 | 1 | 3 | 1 |
| Work table | 2 | 2 | 2 | 3 |
| Warehouse rack | 2 | 2 | 2 | 4 |
| Cart | 0 | 0 | 0 | 1 |
| Total retained | 5 | 5 | 7 | 9 |
| Forklift-like rejected | 3/6 | 3/5 | 5/7 | 5/7 |

### 八.C. 拒绝画像

| 拒绝原因 | 计数 | 解释 |
|---|---:|---|
| dynamic_contamination | 16 | 叉车类簇被反复检测，但 dynamic-agent 状态占优。 |
| single_session_or_low_session_support | 13 | 缺少跨会话确认。 |
| label_fragmentation | 3 | 标签混杂，检测歧义。 |
| low_support | 2 | 观测太少。 |

动态类拒绝占比：Same-day 50.0%，Cross-day 60.0%，Cross-month 71.4%，Hallway 71.4%。

### 八.D. 准入准则防御（P154-P157）

| 检查 | 结论 |
|---|---|
| P154 参数消融 | min_sessions 和 min_frames 是敏感过滤器；max_dynamic_ratio 因数据双峰而饱和（基础设施 0.00，叉车 >=0.83）。 |
| P155 baseline | naive-all-admit 保留 20 个簇、4 个叉车；purity/support 保留 19 个簇、仍保留 4 个叉车；完整策略保留 5 个簇、0 个叉车。 |
| P156 可视化 | before/after map、生命周期图、decision space 图使准入效果可视化。 |
| P157 类别分析 | forklift 0/4 保留；yellow barrier 40%、work table 50%、warehouse rack 33%。 |

### 八.E. 动态掩码前端结果（P217-P235）

| 证据 | 主要结果 | 保守解释 |
|---|---|---|
| P217 dataset | 237 rows，156/51/30 split，zero overlap，positive pixel rate 0.374176 | 语义 mask 监督训练的干净划分。 |
| P218 compact UNet | val IoU/F1 0.671304/0.803329；test IoU/F1 0.578580/0.733038 | compact frontend 可行，不是独立 GT。 |
| P219 held-out | precision/recall/F1/IoU 0.556007/0.789669/0.604636/0.443210 | 偏 recall，precision 中等。 |
| P220 ORB proxy | 4795 -> 2192，减少 54.2857% | 动态区域特征抑制可行。 |
| P225 sequence | 60 frames，Oct. 12 2022 Aisle_CW indices 480-539；bounded retrained SmallUNet | trajectory-ready only。 |
| P227 baseline | APE 0.088504 -> 0.084529；RPE 0.076145 -> 0.076226；ORB 21030 -> 18617 | 中性 DROID baseline reproduction。 |
| P228 hard gated module | APE 0.088496 -> 0.084705；RPE 0.076145 -> 0.076224；ORB 8969 -> 5073；mean coverage 14.127053% | 原始故事种子；480-539 上 gated-region ORB proxy 下降且轨迹中性。 |
| P233 multi-window hard gate | 120-179 ORB 5927 -> 4820；840-899 ORB 601 -> 1901 | mixed result；不能声称 hard black gating 获得 multi-window support。 |
| P234 hard-gate failure sweep | 840-899 最佳 hard/post-processing variant 仍为 127 -> 1197 | 未找到稳定 post-processing-only hard gate；失败诊断是 boundary keypoint creation。 |
| P235 soft-boundary candidate | `meanfill035_feather5_thr060_cap012_min256`；840-899 ORB 127 -> 0，总 delta 0；DROID 16f dAPE -0.000036/dRPE +0.000007；DROID 60f dAPE +0.000158/dRPE -0.000003；回测 480-539 ORB 1382 -> 188、120-179 ORB 215 -> 20 | 候选 soft-boundary frontend 在有界 smoke 中修复回归窗口；不声明 full benchmark 或 navigation。 |

---

## 九、失败与边界分析

### 九.A. 为什么早期动态 SLAM 轨迹中性

P135-P143 显示，现有 TorWIC Aisle 窗口中的叉车 mask 面积太小，最大每帧覆盖 1.39%，不足以显著影响 DROID-SLAM APE/RPE。DROID-SLAM 内部 flow consistency 也可能已经抑制了小动态异常。该结果是负结果边界，不是管线失败。

### 九.B. P225-P235 边界

| 边界 | 状态 |
|---|---|
| 宽泛动态 SLAM 评测 | 不声明 |
| 导航或规划效果 | 不声明 |
| 独立动态分割真值 | 不声明 |
| learned persistent-map admission | 不声明 |
| P195 | 仍 BLOCKED |
| 60 帧 DROID smoke | 可执行且轨迹中性 |
| ORB predicted/gated-region suppression | proxy 支持，但 hard-boundary 失败模式已记录，P235 只是候选修复 |

正确声明是有界前端 smoke：learned、hard-gated 和 soft-boundary masks 可以在短工业窗口上生成，通过 DROID-SLAM 执行，并用于诊断预测动态区域中的 ORB 特征行为。hard black gate 不能升级为 multi-window support；P235 soft-boundary candidate 仍需更多窗口和独立标签。

### 九.C. 对象维护失败模式

稳定对象若只出现一次或帧数太少，可能被保守拒绝。开放词汇标签碎片化可能导致真实对象被拒绝。基于空间 IoU 的关联在强视角变化或对象移动下可能失败。这些失败模式保留在审计记录中，可随新证据重新评估。

---

## 十、讨论

### 十.A. 为什么不能只看检测置信度

检测置信度表示模型是否看见某物，不表示该物是否值得进入静态地图。P155 purity/support baseline 仍保留全部 4 个叉车，说明仅靠标签一致性和支持度不能解决动态污染。

### 十.B. 为什么分离对象维护与动态掩码

对象维护决定持久语义实体；动态掩码决定哪些像素或特征参与前端/后端估计。未来可以连接两者，但当前证据不足以支持 learned mask 直接参与 persistent-map admission。

### 十.C. 轻量设计取舍

当前方法依赖阈值准则、计数器和 revision 记录，优点是可审计、可复现，缺点是在强视角变化、遮挡和类别歧义时鲁棒性有限。

### 十.D. Aisle 与 Hallway 的角色

Aisle 是主证据链，包含 same-day、cross-day、cross-month。Hallway 是独立迁移分支，不与 Aisle 合并为单个总分，以避免掩盖场景差异。

---

## 十一、局限性

1. 不是完整 lifelong SLAM backend；不做 loop closure、pose optimization、地图压缩或完整长期地图管理。
2. 没有下游任务评估；不测导航成功率、重定位精度、规划质量或任务完成率。
3. 规则关联可能失败；空间 IoU 和标签匹配在大视角变化、遮挡、对象移动下可能脆弱。
4. 依赖开放词汇前端；Grounding DINO [7]、SAM2 [8]、OpenCLIP [9] 的错误会进入观测记录。
5. 动态掩码监督不是独立 GT；P217-P220 使用语义 mask 监督动态标签。
6. P225-P235 是有界 smoke；Oct. 12, 2022 Aisle_CW 证据是短窗口受限前端检查。P233-P234 说明 hard black gating 可能因边界关键点失败，P235 只是候选 soft-boundary 修复。
7. P195 仍 BLOCKED；当前工作没有解决 learned persistent-map admission。
8. 目标期刊格式、引用细节和仓库路径政策仍待定。

---

## 十二、结论

本文给出了动态工业语义分割辅助 SLAM 的厚稿整理版。主贡献是会话级对象准入控制层，它将开放词汇 RGB-D 感知结果转换为可审计的 map-object 决策。在 TorWIC 上，该层在 Aisle 和 Hallway 协议中保留稳定基础设施，并一致拒绝叉车类动态污染。

本文还整合了 P217-P235 动态掩码前端证据。compact learned mask、60 帧 learned-mask package、DROID raw-vs-masked reproduction、P228 confidence/coverage gate、P233-P234 hard-boundary 失败诊断和 P235 soft-boundary candidate 形成一个有界前端故事：hard black gate 在原始窗口能降低 ORB 数量，但在回归窗口会制造边界关键点；mean-fill feathering 在有界 smoke 中移除了该观测回归。该结果增强了论文的动态场景 SLAM 语境，但不越界为宽泛评测、导航、独立 GT 或 learned map-admission 声明。

---

## 参考文献

[1] C. Cadena, L. Carlone, H. Carrillo, Y. Latif, D. Scaramuzza, J. Neira, I. Reid, and J. J. Leonard, "Past, present, and future of simultaneous localization and mapping: Toward the robust-perception age," *IEEE Trans. Robot.*, vol. 32, no. 6, pp. 1309-1332, 2016. DOI: 10.1109/TRO.2016.2624754.

[2] B. Bescos, J. M. Facil, J. Civera, and J. Neira, "DynaSLAM: Tracking, mapping, and inpainting in dynamic scenes," *IEEE Robot. Autom. Lett.*, vol. 3, no. 4, pp. 4076-4083, 2018. DOI: 10.1109/LRA.2018.2860039.

[3] S. Yang and S. Scherer, "CubeSLAM: Monocular 3-D object SLAM," *IEEE Trans. Robot.*, vol. 35, no. 4, pp. 925-938, 2019. DOI: 10.1109/TRO.2019.2909168.

[4] S. Peng, K. Genova, C. Jiang, A. Tagliasacchi, M. Pollefeys, and T. Funkhouser, "OpenScene: 3D scene understanding with open vocabularies," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2023, pp. 815-824. DOI: 10.1109/CVPR52729.2023.00085.

[5] K. M. Jatavallabhula, A. Kuwajerwala, Q. Gu, M. Omama, T. Chen, S. Li, G. Iyer, S. Saryazdi, N. Keetha, A. Tewari, J. B. Tenenbaum, C. M. de Melo, M. Krishna, L. Paull, F. Shkurti, and A. Torralba, "ConceptFusion: Open-set multimodal 3D mapping," in *Proc. Robot.: Sci. Syst. (RSS)*, 2023. DOI: 10.15607/RSS.2023.XIX.066.

[6] D. Barath, B. Bescos, D. Mishkin, D. Rozumnyi, and J. Matas, "POV-SLAM: Probabilistic object-aware SLAM with semantic mapping benchmarks," in *Proc. Robot.: Sci. Syst. (RSS)*, 2023. DOI: 10.15607/RSS.2023.XIX.069.

[7] S. Liu et al., "Grounding DINO: Marrying DINO with grounded pre-training for open-set object detection," in *Proc. Eur. Conf. Comput. Vis. (ECCV)*, 2024. arXiv: 2303.05499.

[8] N. Ravi et al., "SAM 2: Segment anything in images and videos," arXiv:2408.00714, 2024.

[9] M. Cherti et al., "Reproducible scaling laws for contrastive language-image learning," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2023, pp. 2818-2829. arXiv: 2212.07143.

[10] Z. Teed and J. Deng, "DROID-SLAM: Deep visual SLAM for monocular, stereo, and RGB-D cameras," in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 34, 2021. arXiv: 2108.10869.

**软件。** M. Grupp, "evo: Python package for the evaluation of odometry and SLAM," 2017. [Online]. Available: https://github.com/MichaelGrupp/evo

---

## 图表标题与证据索引

**表 1. 对象维护协议证据链。** Same-day Aisle (203/11/5)、Cross-day Aisle (240/10/5)、Cross-month Aisle (297/14/7)、Hallway (537/16/9)。

**表 2. 地图准入准则。** 多会话出现、最小支持、标签一致性、静态占优、最小帧数。

**表 3. 拒绝原因。** dynamic_contamination 16、single_session_or_low_session_support 13、label_fragmentation 3、low_support 2。

**表 4. 准入准则防御。** P154 消融、P155 baseline、P156 可视化、P157 类别保留/拒绝。

**表 5. 动态掩码前端证据。** P217-P235 数据集、模型、ORB proxy、learned-mask sequence、DROID baseline、hard confidence/coverage gate、multi-window failure 证据和 soft-boundary candidate。

**表 6. P225-P235 有界 DROID smoke。** P227 learned-mask baseline、P228 confidence/coverage-gated module、P233-P234 hard-gate failure evidence 和 P235 soft-boundary candidate。按轨迹中性和 ORB proxy diagnostics 报告，不作为 navigation 或 full-benchmark claim。

**图 1-16.** 图像路径沿用英文稿：`paper/figures/torwic_*`。P225-P236 证据见 `paper/export/temporal_masked_sequence_p225.md`、`paper/export/p225_baseline_reproduction_p227.md`、`paper/export/confidence_gated_mask_module_p228.md`、`paper/export/p228_paper_story_results.md`、`paper/export/gated_mask_multi_window_p233.md`、`paper/export/gated_mask_failure_sweep_p234.md`、`paper/export/soft_boundary_mask_p235.md`、`paper/export/thick_results_lock_p236.md`。
