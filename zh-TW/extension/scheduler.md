# Scheduler 擴充套件

預設排程器不滿足需求時，可以為 `kube-scheduler` 編寫排程外掛，也可以執行獨立的排程器。Pod 的 `spec.schedulerName` 指定負責該 Pod 的排程器；叢集中的不同排程器必須使用不同名稱。

## 擴充套件排程器

優先使用 Kubernetes 穩定的 [Scheduling Framework](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)。外掛編譯進 `kube-scheduler`，並在 `PreFilter`、`Filter`、`Score`、`Bind` 等擴充套件點實現所需邏輯。透過 [Scheduler Configuration](https://kubernetes.io/docs/reference/scheduling/config/) 設定外掛和排程器 profile；需要同一排程器提供不同策略時，可以用多個 profile，而不必另寫輪詢 API 的指令碼。

如果確實需要獨立排程器程序，請參考 Kubernetes 的[設定多個排程器指南](https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-schedulers/)，並為排程器設定專用服務賬號、所需 RBAC 和 Leader Election。

舊版範例曾用 `kubectl proxy` 查詢未排程的 Pod，再直接 POST `Binding` 物件隨機挑選節點。該範例只用於說明早期自定義排程器的概念，不是生產用排程器實現：它沒有執行排程框架的過濾與評分流程，也不檢查資源、汙點、親和性或其他 Pod 約束。不要用該指令碼部署排程器。

## 使用自定義排程器

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  # 选择使用自定义调度器 my-scheduler
  schedulerName: my-scheduler
  containers:
  - name: nginx
    image: registry.k8s.io/pause:3.10.2
```
