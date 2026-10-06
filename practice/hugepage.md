# HugePages

Kubernetes 将 Linux HugePages 作为可调度资源向 Pod 暴露。v1.37 不需要旧教程中的 `HugePages=true` feature gate，也不需要在每个 Pod 启动时手工挂载 `hugetlbfs`。节点内核和发行版必须先配置所需页大小的 HugePages；节点向 Kubernetes 报告可分配容量后，调度器才能放置请求该资源的 Pod。具体的预分配方法依操作系统和节点引导配置而异。
HugePages 的历史功能演进始于 Kubernetes v1.9 Alpha、v1.10 Beta；旧发行版的 feature gate 和节点操作说明不应沿用到 v1.37。

检查节点可分配的页大小和容量：

```bash
kubectl describe node <node-name>
```

清单中的资源名按节点实际提供的页大小填写，如 `hugepages-2Mi`。HugePages 不能超额分配；request 与 limit 必须相等（仅给出 limit 时 Kubernetes 会将其作为 request）。

## 示例：申请 2 MiB HugePages

只有当节点已提供至少 100 MiB 的 `hugepages-2Mi` 容量时，下面的 Pod 才能调度。此清单只演示资源申请和 HugePages-backed `emptyDir`；应用须自行按 Linux HugePages 接口使用挂载的内存。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hugepages-example
spec:
  containers:
  - name: example
    image: busybox:1.37.0
    command: ["sh", "-c", "sleep 3600"]
    volumeMounts:
    - name: hugepages
      mountPath: /hugepages
    resources:
      requests:
        cpu: "100m"
        memory: "100Mi"
        hugepages-2Mi: "100Mi"
      limits:
        cpu: "500m"
        memory: "200Mi"
        hugepages-2Mi: "100Mi"
  volumes:
  - name: hugepages
    emptyDir:
      medium: HugePages-2Mi
```

不同 HugePages 页大小应使用相应的资源名和卷 medium，例如 `hugepages-1Gi` 与 `HugePages-1Gi`。通用 `medium: HugePages` 仅适用于 Pod 请求一种 HugePages 大小。HugePages-backed `emptyDir` 不得超过 Pod 请求的该类 HugePages；同一 Pod 中各容器的隔离与资源额度按各容器资源声明执行。

使用 `shmget(SHM_HUGETLB)` 的程序还需要与节点 `/proc/sys/vm/hugetlb_shm_group` 匹配的 supplemental group。需要按 namespace 控制用量时，可在 ResourceQuota 中使用 `hugepages-<size>` 资源名。

更多字段与调度条件见 [Kubernetes Manage HugePages](https://kubernetes.io/docs/tasks/manage-hugepages/scheduling-hugepages/) 和[资源管理文档](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#huge-pages)。
