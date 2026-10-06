# CoreDNS 與歷史 kube-dns

Kubernetes v1.37.1 的 kubeadm 預設部署 CoreDNS **1.14.6**。新建叢集時不要另行套用本頁早期 kube-dns Deployment 或重複安裝第二套 DNS。kubeadm 建立的 CoreDNS 在 CNI 安裝前不會正常工作；先完成 Pod network，再檢查：

```bash
kubectl -n kube-system get deploy,pods -l k8s-app=kube-dns
kubectl -n kube-system rollout status deployment/coredns
```

kubeadm 映像檔列表、設定和 CoreDNS Corefile 可從官方 [kubeadm 文件](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)與 [CoreDNS 文件](https://coredns.io/manual/toc/)查閱。變更副本數、外掛或轉發目標前，備份並檢查現有 Corefile；修改預設映像檔版本時先核實 Kubernetes 與 CoreDNS 的相容性。驗證服務發現時可從實際 workload namespace 查詢叢集 Service 的 DNS 名稱。

> **歷史說明：** 舊版 Kubernetes 使用 kube-dns，並由獨立的 Deployment/Service 及早期 addon-manager YAML 管理。該歷史設定不適用於 v1.37.1；本手冊不保留舊 YAML 和下載命令，避免誤部署重複 DNS 服務。