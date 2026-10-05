# Kubernetes网络

本章介绍Kubernetes的网络模型以及常见插件的原理和使用方法。

## Kubernetes v1.37.1 注意事项

Kubernetes 本身不提供一个适用于所有集群的默认 Pod CNI。为集群选定并安装一种主要 CNI 实现，并确认其发行版明确支持 Kubernetes v1.37；不要把不同 CNI 的安装清单叠加部署。CNI 二进制插件、负责集群 Pod 网络的 CNI 实现，以及 kube-proxy/eBPF 服务转发是不同层次的组件。

截至 2026-10-05，Calico v3.33.0 官方兼容矩阵包含 Kubernetes v1.37。Cilium v1.20 官方矩阵只保证 Kubernetes v1.33–1.36；Flannel v0.28.9 的 Kubernetes v1.37 支持未获官方矩阵确认。先核对当前发行说明及网络插件对 Pod CIDR、内核和 kube-proxy 替代方式的要求，再安装。

本章的 [网络插件概览](../extension/network/README.md) 记录当前版本与逐产品安装来源；本目录中的其他插件页面包含历史背景，不应直接当作当前部署指引。
