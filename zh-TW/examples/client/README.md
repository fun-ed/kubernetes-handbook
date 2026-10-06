# Kubernetes 用戶端範例

本目錄彙整多種程式語言的 Kubernetes 用戶端範例。Go informer 範例位於
`informer/`，其 `client-go` 與 Kubernetes Go 模組版本為 v0.37.1，最低 Go
版本為 1.26.0。

在可存取 Kubernetes API 的環境中，從該模組目錄執行：

```sh
cd examples/client/informer
go run . --kubeconfig "$HOME/.kube/config"
```

此程式會監聽所有命名空間的 Pod 事件，不會修改叢集資源；使用的身分需要
`pods` 的 `list` 和 `watch` 權限。傳送 SIGINT 或 SIGTERM 可正常停止 informer。
