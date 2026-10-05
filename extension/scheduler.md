# Scheduler 扩展

默认调度器不满足需求时，可以为 `kube-scheduler` 编写调度插件，也可以运行独立的调度器。Pod 的 `spec.schedulerName` 指定负责该 Pod 的调度器；集群中的不同调度器必须使用不同名称。

## 扩展调度器

优先使用 Kubernetes 稳定的 [Scheduling Framework](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)。插件编译进 `kube-scheduler`，并在 `PreFilter`、`Filter`、`Score`、`Bind` 等扩展点实现所需逻辑。通过 [Scheduler Configuration](https://kubernetes.io/docs/reference/scheduling/config/) 配置插件和调度器 profile；需要同一调度器提供不同策略时，可以用多个 profile，而不必另写轮询 API 的脚本。

如果确实需要独立调度器进程，请参考 Kubernetes 的[配置多个调度器指南](https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-schedulers/)，并为调度器配置专用服务账号、所需 RBAC 和 Leader Election。

旧版示例曾用 `kubectl proxy` 查询未调度的 Pod，再直接 POST `Binding` 对象随机挑选节点。该示例只用于说明早期自定义调度器的概念，不是生产用调度器实现：它没有执行调度框架的过滤与评分流程，也不检查资源、污点、亲和性或其他 Pod 约束。不要用该脚本部署调度器。

## 使用自定义调度器

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

