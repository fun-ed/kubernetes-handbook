# Kubernetes Feature Gates

Feature gate 是逐组件控制 Alpha/Beta 功能的 `名称=true|false` 开关。可用名称、阶段、默认值和生命周期会随 Kubernetes 版本改变；不要从旧版本配置中复制整串 gate。

当前目标为 Kubernetes v1.37.1。以下只是官方 v1.37 表格中的少量示例，不是推荐的生产开关清单：

| Gate | v1.37 阶段与默认值 | 说明 |
| --- | --- | --- |
| `MemoryQoS` | Beta，默认 `true` | v1.37 从 Alpha 转为 Beta；按 kubelet 文档及工作负载特征验证内存控制效果。 |
| `HPAScaleToZero` | Beta，默认 `true` | v1.37 从 Alpha 转为 Beta；需确认 HPA 配置和目标指标源满足该功能要求。 |
| `KubeletInUserNamespace` | Beta，默认 `true` | v1.37 从 Alpha 转为 Beta；仅对相应 kubelet/user namespace 部署有效。 |
| `AtomicWriteVolumeUserFields` | Alpha，默认 `false` | v1.37 新增 Alpha gate；仅在理解该功能限制后才评估启用。 |
| `AllowUnsafeMalformedObjectDeletion` | Beta，默认 `true` | v1.37 从 Alpha 转为 Beta。名称包含 unsafe；不要仅为消除对象删除错误而随意更改此安全相关行为。 |

阶段和默认值引用自 [Kubernetes v1.37 Feature Gates 官方表格](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/)。该表格会随发布更新。部署时还需查看实际组件的 feature-gate 支持情况，因为一个 gate 不一定适用于所有组件。

## 配置原则

- 只在功能仍处于 Alpha/Beta 且官方文档要求时配置 gate。GA 功能通常不再需要 gate；已移除 gate 会导致启动参数无效或被拒绝。
- 在所有相关组件上协调配置，例如 API server 和对应控制器；逐步发布期间确认组件版本和 gate 组合兼容。
- 修改 kubeadm 管理的控制平面时，通过受支持的 kubeadm 配置/升级流程变更，避免直接编辑生成的静态 Pod manifest 后失去配置一致性。
- 上线前使用与目标 Kubernetes **同 minor 版本**的官方 gate 表格、API 文档和发行说明审核；不要把本页示例当作长期兼容承诺。

查看完整的 [Feature Gates](https://kubernetes.io/docs/reference/command-line-tools-reference/feature-gates/) 表格和 [Configure Feature Gates](https://kubernetes.io/docs/tasks/administer-cluster/feature-gates/) 操作指南。