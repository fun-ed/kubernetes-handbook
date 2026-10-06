# Device Plugin 與 Dynamic Resource Allocation

Kubernetes Device Plugin 為 GPU、FPGA、高效能 NIC 等硬體裝置提供節點級擴充套件資源；Dynamic Resource Allocation（DRA）提供更靈活的裝置 class、claim 和裝置選擇機制。二者都是當前 API 路徑：應按裝置驅動支援的介面選擇，不能把 DRA 當作所有 Device Plugin 的無縫替換。

## Device Plugin

Device Plugin 自 Kubernetes v1.26 起穩定。無需設定舊的 `DevicePlugins=true` feature gate；該 gate 已完成生命週期。裝置廠商外掛通常以 DaemonSet 部署，註冊 kubelet 的 gRPC 服務，並將資源以 `vendor-domain/resource` 名稱釋出到 Node status。節點裝置目錄需要 hostPath 與特權存取，具體 RBAC、runtime、驅動和核心依賴須按裝置廠商文件設定。

Device Plugin 暴露的 extended resource 通常只能以整數請求，不能 overcommit 或在多個容器間共享。Pod 在 `resources.limits` 中申請數量（如需 `requests`，必須與 `limits` 相等）：

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

Kubernetes v1.37 Device Plugin API 的註冊、socket、重啟恢復及監控約束見[官方 Device Plugins 文件](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)；裝置外掛版本和 kubelet API version 應遵循廠商提供的相容說明。

## NVIDIA GPU 外掛

舊文中的 `git clone` 未固定版本、從 `master` 下載 DaemonSet、手工建置 `nvidia-device-plugin:1.0.0` 及 `nvidia-docker2` / Docker runtime 設定都不是 Kubernetes v1.37.1 的部署指南，不要執行。v1.37 節點使用受支援的 CRI runtime；NVIDIA 驅動、Container Toolkit、裝置外掛或 GPU Operator 的安裝方式以 NVIDIA 當前文件為準。

截至 2026-10-05，NVIDIA GPU Operator **v26.7.1** 的官方平台矩陣覆蓋 Kubernetes **1.33–1.37**，元件矩陣為該版列出 NVIDIA Device Plugin **v0.20.1**。這屬於 Operator 管理下的相容證據；單獨部署 Device Plugin v0.20.1 的 README 僅給最低 Kubernetes 版本，沒有同樣的 1.37 測試矩陣。該元件矩陣對 NVIDIA DRA Driver v0.5.0 的列值屬於 GPU Operator v26.7.0，不應據此聲稱 v26.7.1 包含該 DRA Driver。詳見 [GPU Operator 26.7.1 平台支援表](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/platform-support.html)、[Device Plugin v0.20.1](https://github.com/NVIDIA/k8s-device-plugin/releases/tag/v0.20.1) 和[版本相容表](../setup/component-versions.md#可安裝外掛與附加元件)。

## Dynamic Resource Allocation（DRA）

Dynamic Resource Allocation（DRA）核心功能和 `resource.k8s.io/v1` API 自 Kubernetes v1.34 起 GA；`DynamicResourceAllocation` 核心 feature gate 自 v1.35 起鎖定為啟用，鎖定與 GA 是不同階段。DRA 核心 API 包括 `DeviceClass`、`ResourceClaim` 和 `ResourceClaimTemplate`。不要照抄 v1.33 的 Alpha 標記或 `resource.k8s.io/v1alpha2` API。v1.37 叢集預設啟用 DRA 核心 API，但仍需安裝相容的 DRA-capable device driver，並按 driver 文件建立 `DeviceClass`；僅有傳統 Device Plugin 不會自動提供 DRA。詳見 [v1.34 DRA GA 釋出說明](https://kubernetes.io/blog/2025/09/01/kubernetes-v1-34-dra-updates/) 和 [v1.35.0 釋出說明](https://github.com/kubernetes/kubernetes/blob/v1.35.0/CHANGELOG/CHANGELOG-1.35.md)。

下例展示一個 DeviceClass、申請一個裝置的 ResourceClaim，以及 Pod 如何引用 claim。`driver.example.com` 與屬性欄位必須按驅動實際釋出的 `ResourceSlice` 替換；範例應用映像檔也需替換。

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

Pod `spec.resourceClaims` 中的 claim 名稱是容器 `resources.claims[].name` 使用的別名；Pod 中已建立的 `ResourceClaim` 透過 `resourceClaimName` 引用。容器 `resources.claims[].request` 仍是有效的可選欄位，用於選擇該 claim 中的某個 request，值應匹配 `spec.devices.requests[].name`，而不是 claim 名稱。舊範例中的 `ResourceClass` 和 `resource.k8s.io/v1alpha2` 不是當前 schema。參見 [Kubernetes v1.37.1 core API 定義](https://github.com/kubernetes/kubernetes/blob/v1.37.1/staging/src/k8s.io/api/core/v1/types.go#L3107-L3115)。DRA 資源設定、節點前置要求與使用範例見[官方 DRA 概念文件](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/)、[叢集設定](https://kubernetes.io/docs/tasks/configure-pod-container/assign-resources/set-up-dra-cluster/)及[工作負載範例](https://kubernetes.io/docs/tasks/configure-pod-container/assign-resources/allocate-devices-dra/)。

## 參考資料

* [Kubernetes Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
* [Kubernetes Dynamic Resource Allocation](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/)
* [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/)
* [NVIDIA Kubernetes Device Plugin](https://github.com/NVIDIA/k8s-device-plugin)
