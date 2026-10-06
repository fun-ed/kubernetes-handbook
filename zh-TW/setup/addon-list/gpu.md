# Kubernetes GPU 工作負載

Kubernetes GPU 資源由裝置外掛報告給 kubelet；排程器使用資源名（常見 NVIDIA 裝置為 `nvidia.com/gpu`）為 Pod 分配資源。v1.37 叢集還需選擇與節點 OS、核心、GPU 型號、驅動和 Kubernetes release 匹配的廠商外掛/管理器。

截至 2026-10-05，NVIDIA GPU Operator 最新已核實的 release 為 [26.7.1](https://github.com/NVIDIA/gpu-operator/releases/tag/v26.7.1)；其 [26.7 平台支援矩陣](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/platform-support.html)明確列出 Kubernetes v1.33–v1.37。部署前仍須按矩陣核對節點 OS、GPU 型號、驅動、容器執行時和其他平台要求。獨立的 [NVIDIA Kubernetes Device Plugin v0.20.1](https://github.com/NVIDIA/k8s-device-plugin/releases/tag/v0.20.1) 資料只給出 Kubernetes 最低版本要求，並非完整的版本相容矩陣；不可據此推斷全部 v1.37 平台組合均受支援。

## 工作負載設定

當已安裝並驗證裝置外掛後，Pod 可在 `resources.limits` 請求 GPU，例如：

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

排程前確認節點 `Allocatable` 顯示 GPU 資源，資源申請值為整數，並檢查 image 對目標 GPU/driver 的執行時支援。容器驅動、工具包、device plugin 或 operator 的具體部署與安全權限按 NVIDIA 當前說明執行；不要將 GPU DaemonSet 全面授予叢集管理員權限。

> **歷史說明：** 本頁舊範例固定到 Kubernetes v1.6–1.9、`alpha.kubernetes.io/nvidia-gpu`、Docker/nvidia-docker2、舊 GCE daemonset 和已淘汰的 `k8s.gcr.io/cuda-vector-add`。這些舊節點、API、驅動安裝和 `apt-key` 命令不適用於 v1.37.1。