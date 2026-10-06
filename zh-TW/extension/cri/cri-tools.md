# CRI-tools

通常，容器引擎會提供一個命令列工具來幫助使用者除錯容器應用並簡化故障排錯。比如使用 Docker 作為容器執行時的時候，可以使用 `docker` 命令來檢視容器和映像檔的狀態，並驗證容器的設定是否正確。但在使用其他容器引擎時，推薦使用 `crictl` 來替代 `docker` 工具。

截至 2026-10-05，cri-tools 最新穩定版本為 [v1.37.0](https://github.com/kubernetes-sigs/cri-tools/releases/tag/v1.37.0)。該版本線對應 Kubernetes v1.37，但這不代表任意 CRI 執行時都透過了相容性測試。Kubernetes v1.37.1 儲存庫的依賴清單為特定引導指令碼固定 crictl v1.36.0；這不是 cri-tools 的最新發布版本。

在節點上設定執行時端點，避免 `crictl` 猜測執行時：

```yaml
# /etc/crictl.yaml
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
```

CRI-O 使用 `unix:///var/run/crio/crio.sock`。更改端點後，可用 `crictl info` 檢查執行時是否提供 CRI v1 服務，再用 `crictl pods`、`crictl ps -a`、`crictl images`、`crictl logs <container-id>` 或 `crictl exec -it <container-id> sh` 診斷容器。

官方資料：[cri-tools v1.37.0 釋出](https://github.com/kubernetes-sigs/cri-tools/releases/tag/v1.37.0)、[crictl 文件](https://github.com/kubernetes-sigs/cri-tools/blob/v1.37.0/docs/crictl.md)、[Kubernetes 節點 crictl 指南](https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/)。


`crictl` 是 [cri-tools](https://github.com/kubernetes-sigs/cri-tools) 提供的 CRI 除錯客戶端。它繞過 kubelet，直接呼叫容器執行時的 CRI 服務；不能替代 `kubectl`，也不應作為日常工作負載建立工具。節點上手工建立的 Pod 或容器不受 kubelet 管理。
`critest` 是 cri-tools 提供的 CRI 整合測試工具。僅在開發或驗證執行時的測試環境執行；不要把它當作生產節點的排障工具。當前文件見 [cri-tools v1.37.0](https://github.com/kubernetes-sigs/cri-tools/tree/v1.37.0)。

`crictl` 提供 `pods`、`ps`、`images`、`inspect`、`logs` 和 `exec` 等診斷命令。只用它檢視或排查由 kubelet 管理的執行時物件。不要在 Kubernetes 節點上用 `crictl runp` 或 `crictl create` 管理應用 Pod。

> 下列命令輸出來自舊節點和舊映像檔。它們只展示 `crictl` 的互動形式，不表示這些映像檔、容器或欄位適用於當前 Kubernetes。

> 舊節點的容器、映像檔 ID 與輸出已移至[封存的診斷輸出](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/extension/cri/cri-tools.md)；上方列出的 crictl 命令可用於目前受管理的容器診斷。

## 參考文件

* [Debugging Kubernetes nodes with crictl](https://kubernetes.io/docs/tasks/debug/debug-cluster/crictl/)
* [https://github.com/kubernetes-sigs/cri-tools](https://github.com/kubernetes-sigs/cri-tools)
