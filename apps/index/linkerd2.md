# Linkerd

Linkerd 是 Kubernetes 服务网格。早期 Linkerd 2.x 章节中的 `linkerd install` 输出、Controller workload、Dashboard 路径、Emojivoto 清单与性能数字来自数年前的版本，不是当前安装说明。

> **发布状态（截至 2026-10-05）**：独立 Linkerd OSS 稳定版自 2024 年 2 月后没有新的稳定 release；GitHub 的 `stable-2.20` 是 Git milestone/tag，不代表可下载的稳定发行包。当前可见的 OSS 发行线为 edge 26.9.3，不应称为生产稳定版。需要生产支持时，核对官方当前发布说明或单独评估提供稳定发行版与支持服务的供应商；不要照抄本页旧 `linkerd install` 命令。

来源：[Linkerd OSS releases](https://github.com/linkerd/linkerd2/releases)、[官方安装文档](https://linkerd.io/2/getting-started/)、[官方概览](https://linkerd.io/2/overview/)。本次没有找到 OSS edge/stable 对 Kubernetes v1.37 的明确兼容声明，因此不推荐在本手册目标集群 v1.37.1 上部署。

## 评估前检查

1. 确认所采用的发行版确实有可验证的 release artifact；不要把 Git milestone 或 nightly/edge build 当作稳定版。
2. 逐项核对发行说明中的 Kubernetes、CNI、内核、代理注入和 upgrade 支持范围。
3. 在测试集群验证 CLI、控制平面、数据平面代理、证书轮换和卸载流程，再制定生产升级及回滚方案。

本页旧的集群清单、`deployment.extensions` 输出、动态下载的 Emojivoto YAML、旧指标和 tap 示例只作为 Linkerd 2.x 历史演示保留；不要对当前集群执行。
