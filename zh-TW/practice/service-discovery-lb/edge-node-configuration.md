# 叢集入口與外部 VIP

> **舊範例不可照抄**：本頁後面的原始 Keepalived、IPVS、手工修改 Traefik DaemonSet、測試網段 IP 與 hostPort 設定來自舊叢集，不是 Kubernetes v1.37 的可部署高可用方案。不要在生產節點照搬這些位址、systemd 設定或 `ipvsadm` 操作。

## 選擇入口架構

- 雲平台通常優先使用受支援的 `Service` type `LoadBalancer` 或平台 Ingress/Gateway 實現，由雲控制面分配並維護入口位址。
- 裸機叢集可評估受維護且與當前 Kubernetes/CNI 相容的 LoadBalancer 實現，或由平台網路團隊提供外部 VIP/負載平衡。確認位址池、路由公告、健康檢查、故障切換與防火牆規則。
- 若在叢集外執行代理並轉發到 NodePort/LoadBalancer，應將節點維護、後端健康檢查、源位址保留和安全策略作為基礎設施設定管理。

選擇方案時同時考慮故障域、L2/L3 網路拓撲、Pod CIDR 可達性、CNI、kube-proxy 模式與雲/機房責任邊界。VIP 漂移不是服務高可用本身；必須驗證代理到各節點的健康檢查、成員變更時的摘除行為和客戶端重試策略。

## Kubernetes 側檢查

```bash
kubectl get nodes -o wide
kubectl get services --all-namespaces -o wide
kubectl get ingressclass
```

Kubernetes v1.35 起 IPVS kube-proxy 模式已棄用；nftables backend 已 GA，但不會自動成為預設值。升級或改用 nftables 前，應核對節點核心、CNI、發行版 kube-proxy 設定和官方遷移指南；不要為實現 VIP 而直接在節點上操作 IPVS 表。

原文的 Keepalived 三節點實驗、Traefik 舊 RBAC/Deployment、IPVS 與 `hostPort` 細節僅供理解舊架構。實際部署請使用當前平台和入口控制器各自維護的設定方式，不要把舊實驗位址視為預設方案。
