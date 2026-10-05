# GPU 工作负载

Kubernetes 可通过 device plugin 暴露厂商 GPU 资源；本文以 NVIDIA GPU 为例。GPU 能否调度取决于节点驱动、CRI runtime、device plugin、设备型号、容器 CUDA runtime 和目标 Kubernetes 版本的共同兼容性。

## NVIDIA GPU Operator（截至 2026-10-05）

NVIDIA GPU Operator **v26.7.1** 于 2026-09-23 发布。NVIDIA 版本专属 platform support 矩阵明确列出 Kubernetes **1.33–1.37**，因此该 Operator 版本覆盖本手册目标 Kubernetes v1.37.1；仍需按矩阵逐项确认具体 OS、云平台、GPU 型号与部署拓扑。

- [GPU Operator v26.7.1 release](https://github.com/NVIDIA/gpu-operator/releases/tag/v26.7.1)
- [v26.7 platform support matrix](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/platform-support.html)
- [v26.7.1 installation guide](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/getting-started.html)

GPU Operator 的默认部署可管理 NVIDIA 驱动、Container Toolkit、NVIDIA Device Plugin、DCGM Exporter、MIG Manager 和 Node Feature Discovery。集群节点应使用 CRI-O 或 containerd；不要安装 Docker Engine 或旧 `nvidia-docker2` 来满足 Kubernetes GPU 调度。

若集群启用 Pod Security Admission，Operator namespace 需要 `privileged` enforcement，以允许受信任的节点级组件运行。该例外仅应用于单独的 Operator namespace：

```bash
kubectl create namespace gpu-operator
kubectl label --overwrite namespace gpu-operator \
  pod-security.kubernetes.io/enforce=privileged
```

下面按 NVIDIA 官方推荐使用带固定版本的 OCI chart 安装；也可使用相同版本的经典 Helm repository chart，具体配置以 v26.7.1 文档为准：

```bash
helm install --wait gpu-operator \
  --namespace gpu-operator \
  oci://nvcr.io/nvidia/cloud-native-charts/gpu-operator \
  --version=v26.7.1
```

默认配置会在 GPU worker 节点安装所需组件。若 GPU driver 已由节点镜像或平台管理，或集群已有 Node Feature Discovery，应按官方 guide 调整 `ClusterPolicy`，不要再启动另一套 driver/NFD 管理器。使用 driver container 时，相关 GPU 节点必须符合 NVIDIA 对 OS 的要求。

安装后确认 Operator 健康、`ClusterPolicy` ready，并确认节点已公布可分配 GPU：

```bash
kubectl get pods -n gpu-operator
kubectl get clusterpolicy
kubectl describe node <gpu-node>
```

在 Node 的 `Capacity`/`Allocatable` 中检查 `nvidia.com/gpu`。缺失时先检查 GPU 驱动、Operator validator、device-plugin 日志与平台支持表，不要直接在 kubelet manifest 中手工注入设备文件。

## 请求传统 device-plugin GPU 资源

标准 device plugin 模式将 GPU 作为扩展资源 `nvidia.com/gpu` 注册。请求数量写在容器的 `resources.limits` 中；镜像需使用与 GPU driver/CUDA 兼容的固定版本：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cuda-vectoradd
spec:
  restartPolicy: OnFailure
  containers:
    - name: cuda-vectoradd
      image: nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda12.5.0-ubuntu22.04
      resources:
        limits:
          nvidia.com/gpu: 1
```

在测试 namespace 中应用后检查 Pod 日志：

```bash
kubectl apply -f cuda-vectoradd.yaml
kubectl logs pod/cuda-vectoradd
```

标准 device-plugin 分配的是整数设备；GPU sharing、MIG profile、time-slicing 与 MPS 由 NVIDIA 驱动及 Operator 配置控制，不能只靠把 `nvidia.com/gpu` 数量设成小数来实现。按照目标硬件与工作负载性能需求单独验证这些模式。

## Dynamic Resource Allocation（DRA）

Kubernetes DRA 自 v1.34 起 GA，核心 feature gate `DynamicResourceAllocation` 自 v1.35 起锁定启用，支持 device-class、ResourceClaim 与驱动提供的 ResourceSlice 等资源。但 DRA GPU 清单依赖实际安装的 GPU driver/DRA driver 定义的 `DeviceClass` 和 schema；不能用通用伪造的 ResourceClass parameters 代替。使用前确认 NVIDIA GPU Operator 对目标平台提供的 DRA 功能与文档，再按[Kubernetes DRA 指南](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/)和[Operator 26.7 文档](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/)编写与验证清单。

## 旧示例说明

本页早期内容曾要求启用已过时的 `DevicePlugins` feature gate、将 kubelet 绑定 Docker、安装旧版 `nvidia-docker2`、手工挂载宿主机驱动文件，或使用旧 `alpha.kubernetes.io/nvidia-gpu` API。这些均不是当前安装方式。先前的 DRA 示例使用 `resource.k8s.io/v1alpha2`、不存在的 inline `ResourceClass.parameters`/`resourceClaimNames` 字段和未定义的 NVIDIA class；这些 YAML 不符合当前 API schema，已从可运行示例中移除。
