# 在 Kubernetes 上執行 TensorFlow

原章節基於早期 Kubeflow、ksonnet 0.8、`ks` 命令、舊 `gcr.io/kubeflow/*` Notebook 映像檔和未經限制的 `cluster-admin` 綁定。該流程不是 Kubernetes v1.37 的 Kubeflow 安裝方式；舊的管理員綁定、任意使用者名稱/密碼登入和 `ks generate` 命令不能作為當前操作範例，已移除。

當前 Kubeflow 可按需安裝獨立子專案，或使用 Kubeflow Community Distribution / 由維護者提供的發行版。各發行版、Notebook、Trainer、Pipelines 與模型服務元件分別維護版本和 Kubernetes 支援範圍；在 Kubernetes v1.37.1 叢集部署前，應核實所選發行版及元件的相容矩陣和安全升級路徑，而不要把一個元件的版本套用到整個平台。[Kubeflow 安裝選項](https://www.kubeflow.org/docs/started/installing-kubeflow/)

## 工作負載選擇

- Notebook：按當前 [Kubeflow Notebooks 文件](https://www.kubeflow.org/docs/components/notebooks/)部署，並設定組織認可的身分認證、授權、網路存取和資源配額；不要公開未認證的 Notebook 服務。
- 分散式訓練：選擇當前維護的訓練控制器或 [Kubeflow Trainer](https://www.kubeflow.org/docs/components/trainer/)，並針對所選框架和 Kubernetes 版本審查 CRD、Operator 與執行時要求。
- GPU：在部署訓練工作負載前，先確認節點驅動、CRI、GPU Operator/Device Plugin 或 DRA 驅動的支援範圍，見[本手冊 GPU 章節](../gpu.md)。
- 模型服務：單獨核實當前服務元件的 API、認證與 Kubernetes 支援範圍，不再使用舊 `ks generate tf-serving` 範例。

容器映像檔應包含與訓練任務匹配的 TensorFlow、Python/CUDA 和應用依賴；將映像檔釋出到叢集可存取的 registry，並按供應鏈策略固定 digest。為每個控制器和工作負載設定最小權限的 ServiceAccount、CPU/記憶體/GPU 資源以及適當的 Pod 安全策略。具體 API 和安裝步驟以所選專案的官方版本文件為準。

參考：[TensorFlow 官方文件](https://www.tensorflow.org/)、[Kubeflow 子專案文件](https://www.kubeflow.org/docs/components/)。
