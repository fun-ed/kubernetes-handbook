# ReplicaSet

`ReplicaSet` 確保符合 selector 的 Pod 副本數接近期望值。應用程式通常由 `Deployment` 管理，而不是直接建立 ReplicaSet；Deployment 提供宣告式 rollout、revision 歷程及回復功能。

`apps/v1` 是目前的 ReplicaSet API。舊版 `extensions/v1beta1`、`apps/v1beta1` 和 `apps/v1beta2` API 已移除。舊版 ReplicaSet/Guestbook 教學及其不可用的 sample image 已移至[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/objects/replicaset-legacy.md)。

以下僅示範 ReplicaSet selector 與 Pod template 的對應關係。映像檔是截至 2026-10-05 的已驗證 NGINX 穩定標籤 `1.30.5`：

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: frontend
  labels:
    app: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: nginx
          image: nginx:1.30.5
          ports:
            - containerPort: 80
```

`.spec.selector` 必須匹配 Pod template labels，且不得選中其他控制器管理的 Pod。建立後 selector 不可變更。若要調整副本數或更新容器映像檔，請修改 Deployment 的期望狀態並監看 rollout，而不要直接改它管理的 ReplicaSet。

- [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
