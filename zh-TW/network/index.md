# Kubernetes 網路

本章介紹 Kubernetes 的網路模型以及常見外掛的原理和使用方法。

## Kubernetes v1.37.1 注意事項

Kubernetes 本身不提供一個適用於所有叢集的預設 Pod CNI。為叢集選定並安裝一種主要 CNI 實現，並確認其發行版明確支援 Kubernetes v1.37；不要把不同 CNI 的安裝清單疊加部署。CNI 二進位外掛、負責叢集 Pod 網路的 CNI 實現，以及 kube-proxy/eBPF 服務轉發是不同層次的元件。

截至 2026-10-05，Calico v3.33.0 官方相容矩陣包含 Kubernetes v1.37。Cilium v1.20 官方矩陣只保證 Kubernetes v1.33–1.36；Flannel v0.28.9 的 Kubernetes v1.37 支援未獲官方矩陣確認。先核對當前發行說明及網路外掛對 Pod CIDR、核心和 kube-proxy 替代方式的要求，再安裝。

本章的 [網路外掛概覽](../extension/network/README.md) 記錄當前版本與逐產品安裝來源；本目錄中的其他外掛頁面包含歷史背景，不應直接當作當前部署指引。
