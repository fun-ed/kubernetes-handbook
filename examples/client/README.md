# Kubernetes 客户端示例

本目录收集不同语言的 Kubernetes 客户端示例。Go informer 示例位于
`informer/`，其 `client-go` 和 Kubernetes Go 模块版本为 v0.37.1，最低 Go
版本为 1.26.0。

在具备 Kubernetes API 访问权限的环境中，从该模块目录运行：

```sh
cd examples/client/informer
go run . --kubeconfig "$HOME/.kube/config"
```

该程序监听所有命名空间的 Pod 事件，不会修改集群资源；所用身份需要
`pods` 的 `list` 和 `watch` 权限。发送 SIGINT 或 SIGTERM 可正常停止 informer。
