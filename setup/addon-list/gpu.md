# Kubernetes GPU 工作负载

Kubernetes GPU 资源由设备插件报告给 kubelet；调度器使用资源名（常见 NVIDIA 设备为 `nvidia.com/gpu`）为 Pod 分配资源。v1.37 集群还需选择与节点 OS、内核、GPU 型号、驱动和 Kubernetes release 匹配的厂商插件/管理器。

截至 2026-10-05，NVIDIA GPU Operator 最新已核实的 release 为 [26.7.1](https://github.com/NVIDIA/gpu-operator/releases/tag/v26.7.1)；其 [26.7 平台支持矩阵](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/platform-support.html)明确列出 Kubernetes v1.33–v1.37。部署前仍须按矩阵核对节点 OS、GPU 型号、驱动、容器运行时和其他平台要求。独立的 [NVIDIA Kubernetes Device Plugin v0.20.1](https://github.com/NVIDIA/k8s-device-plugin/releases/tag/v0.20.1) 资料只给出 Kubernetes 最低版本要求，并非完整的版本兼容矩阵；不可据此推断全部 v1.37 平台组合均受支持。

## 工作负载配置

当已安装并验证设备插件后，Pod 可在 `resources.limits` 请求 GPU，例如：

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

调度前确认节点 `Allocatable` 显示 GPU 资源，资源申请值为整数，并检查 image 对目标 GPU/driver 的运行时支持。容器驱动、工具包、device plugin 或 operator 的具体部署与安全权限按 NVIDIA 当前说明执行；不要将 GPU DaemonSet 全面授予集群管理员权限。

> **历史说明：** 本页旧示例固定到 Kubernetes v1.6–1.9、`alpha.kubernetes.io/nvidia-gpu`、Docker/nvidia-docker2、旧 GCE daemonset 和已淘汰的 `k8s.gcr.io/cuda-vector-add`。这些旧节点、API、驱动安装和 `apt-key` 命令不适用于 v1.37.1。