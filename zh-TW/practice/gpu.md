# GPU 工作負載

Kubernetes 可透過 device plugin 暴露廠商 GPU 資源；本文以 NVIDIA GPU 為例。GPU 能否排程取決於節點驅動、CRI runtime、device plugin、裝置型號、容器 CUDA runtime 和目標 Kubernetes 版本的共同相容性。

## NVIDIA GPU Operator（截至 2026-10-05）

NVIDIA GPU Operator **v26.7.1** 於 2026-09-23 釋出。NVIDIA 版本專屬 platform support 矩陣明確列出 Kubernetes **1.33–1.37**，因此該 Operator 版本覆蓋本手冊目標 Kubernetes v1.37.1；仍需按矩陣逐項確認具體 OS、雲平台、GPU 型號與部署拓撲。

- [GPU Operator v26.7.1 release](https://github.com/NVIDIA/gpu-operator/releases/tag/v26.7.1)
- [v26.7 platform support matrix](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/platform-support.html)
- [v26.7.1 installation guide](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/getting-started.html)

GPU Operator 的預設部署可管理 NVIDIA 驅動、Container Toolkit、NVIDIA Device Plugin、DCGM Exporter、MIG Manager 和 Node Feature Discovery。叢集節點應使用 CRI-O 或 containerd；不要安裝 Docker Engine 或舊 `nvidia-docker2` 來滿足 Kubernetes GPU 排程。

若叢集啟用 Pod Security Admission，Operator namespace 需要 `privileged` enforcement，以允許受信任的節點級元件執行。該例外僅應用於單獨的 Operator namespace：

```bash
kubectl create namespace gpu-operator
kubectl label --overwrite namespace gpu-operator \
  pod-security.kubernetes.io/enforce=privileged
```

下面按 NVIDIA 官方推薦使用帶固定版本的 OCI chart 安裝；也可使用相同版本的經典 Helm repository chart，具體設定以 v26.7.1 文件為準：

```bash
helm install --wait gpu-operator \
  --namespace gpu-operator \
  oci://nvcr.io/nvidia/cloud-native-charts/gpu-operator \
  --version=v26.7.1
```

預設設定會在 GPU worker 節點安裝所需元件。若 GPU driver 已由節點映像檔或平台管理，或叢集已有 Node Feature Discovery，應按官方 guide 調整 `ClusterPolicy`，不要再啟動另一套 driver/NFD 管理器。使用 driver container 時，相關 GPU 節點必須符合 NVIDIA 對 OS 的要求。

安裝後確認 Operator 健康、`ClusterPolicy` ready，並確認節點已公佈可分配 GPU：

```bash
kubectl get pods -n gpu-operator
kubectl get clusterpolicy
kubectl describe node <gpu-node>
```

在 Node 的 `Capacity`/`Allocatable` 中檢查 `nvidia.com/gpu`。缺失時先檢查 GPU 驅動、Operator validator、device-plugin 日誌與平台支援表，不要直接在 kubelet manifest 中手工注入裝置檔案。

## 請求傳統 device-plugin GPU 資源

標準 device plugin 模式將 GPU 作為擴充套件資源 `nvidia.com/gpu` 註冊。請求數量寫在容器的 `resources.limits` 中；映像檔需使用與 GPU driver/CUDA 相容的固定版本：

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

在測試 namespace 中應用後檢查 Pod 日誌：

```bash
kubectl apply -f cuda-vectoradd.yaml
kubectl logs pod/cuda-vectoradd
```

標準 device-plugin 分配的是整數裝置；GPU sharing、MIG profile、time-slicing 與 MPS 由 NVIDIA 驅動及 Operator 設定控制，不能只靠把 `nvidia.com/gpu` 數量設成小數來實現。按照目標硬體與工作負載效能需求單獨驗證這些模式。

## Dynamic Resource Allocation（DRA）

Kubernetes DRA 自 v1.34 起 GA，核心 feature gate `DynamicResourceAllocation` 自 v1.35 起鎖定啟用，支援 device-class、ResourceClaim 與驅動提供的 ResourceSlice 等資源。但 DRA GPU 清單依賴實際安裝的 GPU driver/DRA driver 定義的 `DeviceClass` 和 schema；不能用通用偽造的 ResourceClass parameters 代替。使用前確認 NVIDIA GPU Operator 對目標平台提供的 DRA 功能與文件，再按[Kubernetes DRA 指南](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/)和[Operator 26.7 文件](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/)編寫與驗證清單。

## 舊範例說明

本頁早期內容曾要求啟用已過時的 `DevicePlugins` feature gate、將 kubelet 綁定 Docker、安裝舊版 `nvidia-docker2`、手工掛載宿主機驅動檔案，或使用舊 `alpha.kubernetes.io/nvidia-gpu` API。這些均不是當前安裝方式。先前的 DRA 範例使用 `resource.k8s.io/v1alpha2`、不存在的 inline `ResourceClass.parameters`/`resourceClaimNames` 欄位和未定義的 NVIDIA class；這些 YAML 不符合當前 API schema，已從可執行範例中移除。
