# kube-proxy 服務代理模式

本頁原有 Kubernetes v1.8 IPVS alpha 本機實驗會強制結束 kube-proxy 並手動變更主機網路，已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/network/ipvs/index.md)。請勿在目前叢集執行封存範例。

在 Kubernetes v1.37 的 Linux 節點上，kube-proxy 可使用 iptables、IPVS 或 nftables 模式。Linux 上 nftables 模式要求 Linux 核心 5.13 或更新版本，自 v1.33 升為 GA，但不是預設模式；未指定模式時，Linux kube-proxy 預設使用 iptables。IPVS 自 v1.35 起棄用，但並非已從所有現有叢集移除。Windows 節點僅提供 `kernelspace` 模式。選擇模式前，核對節點核心／nftables 支援、發行版和 CNI 的相容性，以及是否由 CNI/eBPF 實現取代 kube-proxy；不要在同一叢集任意混用資料平面或手動複製另一模式的規則。詳細模式限制與設定見 [Kubernetes v1.37 虛擬 IP 與 Service Proxy 文件](https://kubernetes.io/docs/reference/networking/virtual-ips/)。

目前 kube-proxy 設定與遷移要求，請依 [Kubernetes v1.37 虛擬 IP 與 Service Proxy 文件](https://kubernetes.io/docs/reference/networking/virtual-ips/)及 [kube-proxy 設定參考](https://kubernetes.io/docs/reference/config-api/kube-proxy-config.v1alpha1/)操作。更換代理模式是叢集網路變更，須依發行版文件於維護流程中進行並驗證 Service 流量；本頁不提供可直接套用至任意叢集的切換命令。
