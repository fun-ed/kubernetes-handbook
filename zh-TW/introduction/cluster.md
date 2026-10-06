# Kubernetes 叢集

![](../.gitbook/assets/architecture%20%287%29.png)

一個 Kubernetes 叢集由控制平面和工作節點組成。控制平面維護叢集狀態並安排工作負載，工作節點執行已排程的 Pod。etcd 儲存叢集狀態；kubelet 透過 CRI 與容器執行時通訊。

詳細介紹請參考 [Kubernetes 架構](../concepts/architecture.md)。

## 多叢集管理

Kubernetes 核心 API 管理單個叢集，不包含 Federation 控制平面。舊版 Kubernetes Federation（KubeFed）已退役。其 API 和舊教程僅作歷史參考，見[歸檔索引](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)。當前多叢集方案由叢集發行版或獨立的多叢集管理工具提供。

## 建立 Kubernetes 叢集

可以參考 [Kubernetes 部署指南](../setup/index.md) 來部署一套 Kubernetes 叢集。而對於初學者或者簡單驗證測試的使用者，則可以使用以下幾種更簡單的方法。

### minikube

[minikube](https://minikube.sigs.k8s.io/docs/start/) 可以在本地啟動 Kubernetes 叢集。具體啟動引數取決於所選驅動和作業系統。啟動後，使用 `kubectl get nodes` 檢查節點，並參考 minikube 文件存取其 Service。
