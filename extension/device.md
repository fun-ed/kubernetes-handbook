# Device Plugin 与 Dynamic Resource Allocation

Kubernetes Device Plugin 为 GPU、FPGA、高性能 NIC 等硬件设备提供节点级扩展资源；Dynamic Resource Allocation（DRA）提供更灵活的设备 class、claim 和设备选择机制。二者都是当前 API 路径：应按设备驱动支持的接口选择，不能把 DRA 当作所有 Device Plugin 的无缝替换。

## Device Plugin

Device Plugin 自 Kubernetes v1.26 起稳定。无需设置旧的 `DevicePlugins=true` feature gate；该 gate 已完成生命周期。设备厂商插件通常以 DaemonSet 部署，注册 kubelet 的 gRPC 服务，并将资源以 `vendor-domain/resource` 名称发布到 Node status。节点设备目录需要 hostPath 与特权访问，具体 RBAC、runtime、驱动和内核依赖须按设备厂商文档配置。

Device Plugin 暴露的 extended resource 通常只能以整数请求，不能 overcommit 或在多个容器间共享。Pod 在 `resources.limits` 中申请数量（如需 `requests`，必须与 `limits` 相等）：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-workload
spec:
  restartPolicy: Never
  containers:
    - name: app
      image: registry.example/gpu-workload:1.0 # 替换为支持目标 GPU 的应用镜像
      resources:
        limits:
          nvidia.com/gpu: 1
```

Kubernetes v1.37 Device Plugin API 的注册、socket、重启恢复及监控约束见[官方 Device Plugins 文档](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)；设备插件版本和 kubelet API version 应遵循厂商提供的兼容说明。

## NVIDIA GPU 插件

旧文中的 `git clone` 未固定版本、从 `master` 下载 DaemonSet、手工构建 `nvidia-device-plugin:1.0.0` 及 `nvidia-docker2` / Docker runtime 配置都不是 Kubernetes v1.37.1 的部署指南，不要执行。v1.37 节点使用受支持的 CRI runtime；NVIDIA 驱动、Container Toolkit、设备插件或 GPU Operator 的安装方式以 NVIDIA 当前文档为准。

截至 2026-10-05，NVIDIA GPU Operator **v26.7.1** 的官方平台矩阵覆盖 Kubernetes **1.33–1.37**，组件矩阵为该版列出 NVIDIA Device Plugin **v0.20.1**。这属于 Operator 管理下的兼容证据；单独部署 Device Plugin v0.20.1 的 README 仅给最低 Kubernetes 版本，没有同样的 1.37 测试矩阵。该组件矩阵对 NVIDIA DRA Driver v0.5.0 的列值属于 GPU Operator v26.7.0，不应据此声称 v26.7.1 包含该 DRA Driver。详见 [GPU Operator 26.7.1 平台支持表](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/platform-support.html)、[Device Plugin v0.20.1](https://github.com/NVIDIA/k8s-device-plugin/releases/tag/v0.20.1) 和[版本兼容表](../setup/component-versions.md#可安装插件与附加组件)。

## Dynamic Resource Allocation（DRA）

Dynamic Resource Allocation（DRA）核心功能和 `resource.k8s.io/v1` API 自 Kubernetes v1.34 起 GA；`DynamicResourceAllocation` 核心 feature gate 自 v1.35 起锁定为启用，锁定与 GA 是不同阶段。DRA 核心 API 包括 `DeviceClass`、`ResourceClaim` 和 `ResourceClaimTemplate`。不要照抄 v1.33 的 Alpha 标记或 `resource.k8s.io/v1alpha2` API。v1.37 集群默认启用 DRA 核心 API，但仍需安装兼容的 DRA-capable device driver，并按 driver 文档创建 `DeviceClass`；仅有传统 Device Plugin 不会自动提供 DRA。详见 [v1.34 DRA GA 发布说明](https://kubernetes.io/blog/2025/09/01/kubernetes-v1-34-dra-updates/) 和 [v1.35.0 发布说明](https://github.com/kubernetes/kubernetes/blob/v1.35.0/CHANGELOG/CHANGELOG-1.35.md)。

下例展示一个 DeviceClass、申请一个设备的 ResourceClaim，以及 Pod 如何引用 claim。`driver.example.com` 与属性字段必须按驱动实际发布的 `ResourceSlice` 替换；示例应用镜像也需替换。

```yaml
apiVersion: resource.k8s.io/v1
kind: DeviceClass
metadata:
  name: example-gpu
spec:
  selectors:
    - cel:
        expression: device.driver == "driver.example.com"
---
apiVersion: resource.k8s.io/v1
kind: ResourceClaim
metadata:
  name: example-gpu-claim
spec:
  devices:
    requests:
      - name: gpu
        exactly:
          deviceClassName: example-gpu
          allocationMode: ExactCount
          count: 1
---
apiVersion: v1
kind: Pod
metadata:
  name: dra-gpu-workload
spec:
  resourceClaims:
    - name: gpu
      resourceClaimName: example-gpu-claim
  containers:
    - name: app
      image: registry.example/gpu-workload:1.0
      resources:
        claims:
          - name: gpu
```

Pod `spec.resourceClaims` 中的 claim 名称是容器 `resources.claims[].name` 使用的别名；Pod 中已创建的 `ResourceClaim` 通过 `resourceClaimName` 引用。容器 `resources.claims[].request` 仍是有效的可选字段，用于选择该 claim 中的某个 request，值应匹配 `spec.devices.requests[].name`，而不是 claim 名称。旧示例中的 `ResourceClass` 和 `resource.k8s.io/v1alpha2` 不是当前 schema。参见 [Kubernetes v1.37.1 core API 定义](https://github.com/kubernetes/kubernetes/blob/v1.37.1/staging/src/k8s.io/api/core/v1/types.go#L3107-L3115)。DRA 资源配置、节点前置要求与使用示例见[官方 DRA 概念文档](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/)、[集群设置](https://kubernetes.io/docs/tasks/configure-pod-container/assign-resources/set-up-dra-cluster/)及[工作负载示例](https://kubernetes.io/docs/tasks/configure-pod-container/assign-resources/allocate-devices-dra/)。

## 参考资料

* [Kubernetes Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
* [Kubernetes Dynamic Resource Allocation](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/)
* [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/)
* [NVIDIA Kubernetes Device Plugin](https://github.com/NVIDIA/k8s-device-plugin)
