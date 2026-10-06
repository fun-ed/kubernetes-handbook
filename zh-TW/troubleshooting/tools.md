# 排錯工具

## Kubernetes API 與工作負載

優先使用 `kubectl` 檢視 API 物件、Events 和容器日誌：

```bash
kubectl get pods -A -o wide
kubectl describe pod <pod-name> -n <namespace>
kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp
kubectl logs <pod-name> -n <namespace> -c <container-name> --previous --timestamps
```

確認 Namespace 和容器名稱後再執行命令。排查 Service 時檢查 selector、EndpointSlices 及 NetworkPolicy；不要假設資料平面由某一種 kube-proxy 模式實現。

## CRI 執行時與節點

容器執行時排錯使用 CRI 工具，而不是 Docker 專用命令。`crictl` 應在授權的節點管理環境中執行，並設定為連線該節點實際使用的 CRI endpoint：

```bash
sudo crictl info
sudo crictl pods
sudo crictl ps -a
sudo crictl images
```

不同執行時、發行版的服務名稱、socket 和日誌路徑不同；按其維護文件檢查。節點系統服務可透過發行版提供的受控存取方式讀取 `journalctl` 日誌。不要在普通工作負載中掛載 Docker socket、CRI socket、主機根目錄或 `/var/lib` 執行時資料目錄。

## 網路與效能工具

* `tcpdump`：在獲准的節點或受控除錯環境中分析網路流量；抓包可能包含敏感資料。
* `iproute2`、iptables/nftables 或 IPVS 工具：僅用於檢查叢集實際採用的資料平面實現；不要跨實現複製規則或直接修改主機轉發策略。
* `perf` 和受維護的效能分析工具：需要節點權限，使用前遵循組織的權限、審計和資料保留要求。

安裝或使用第三方代理、eBPF 探針、視覺化 Dashboard 前，應確認其專案仍受維護、相容當前 Kubernetes/核心/CRI 版本、權限滿足最小化原則，並使用經過稽核的部署流程。

## 節點除錯安全

Kubelet、CNI 和核心日誌通常需要節點級權限。優先使用雲服務商或發行版提供的受控管理通道；不要為排錯給節點分配公網 IP，也不要下載並直接執行未經稽核的 `kubectl-node-shell` 外掛。`kubectl debug node` 等除錯流程可能建立高權限資源，只能在獲得授權並理解其主機存取範圍後使用。

## 歷史工具說明

本頁舊版 Docker Socket、sysdig 的 `apt-key` 安裝命令及 Weave Scope 公開 `LoadBalancer` 安裝清單不適合作為 Kubernetes v1.37 的通用建議。不要照搬舊清單；評估第三方工具時，查閱其當前維護狀態、發行版本和安全說明。

更多資訊請參閱 [kubectl 參考](https://kubernetes.io/docs/reference/kubectl/)和 [叢集排錯指南](https://kubernetes.io/docs/tasks/debug/debug-cluster/)。
