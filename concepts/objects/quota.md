# Resource Quota

资源配额（Resource Quotas）是用来限制用户资源用量的一种机制。

它的工作原理为

* ResourceQuota 作用于 Namespace；同一 Namespace 可以有多个配额对象，所有适用配额都会共同限制资源使用
* 当配额限制 `requests.*` 或 `limits.*` 时，Pod 必须提供相应资源值；可使用 [LimitRange](https://kubernetes.io/docs/concepts/policy/limit-range/) 注入默认值
* 配额用尽后，创建或更新请求可能会被拒绝；查看 ResourceQuota 的 `status.used` 与事件进行排查

## 启用与使用资源配额

ResourceQuota 通过 API Server 的准入控制实施。标准 Kubernetes 集群通常启用 ResourceQuota 准入插件；托管发行版可能提供自己的配置方式。确认集群配置后，在目标 Namespace 中创建 `ResourceQuota` 对象。

## 资源配额的类型

* 计算资源，包括 cpu 和 memory
  * cpu, limits.cpu, requests.cpu
  * memory, limits.memory, requests.memory
* 存储资源，包括存储资源的总量以及指定 storage class 的总量
  * requests.storage：存储资源总量，如 500Gi
  * persistentvolumeclaims：pvc 的个数
  * `<storage-class-name>.storageclass.storage.k8s.io/requests.storage` 和 `<storage-class-name>.storageclass.storage.k8s.io/persistentvolumeclaims`：按 StorageClass 限制 PVC 存储量及数量
  * `requests.ephemeral-storage` 和 `limits.ephemeral-storage`：临时存储配额
* 对象数，即可创建的对象的个数
  * pods, replicationcontrollers, configmaps, secrets
  * resourcequotas, persistentvolumeclaims
  * services, services.loadbalancers, services.nodeports

计算资源示例

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
spec:
  hard:
    pods: "4"
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
```

对象个数示例

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-counts
spec:
  hard:
    configmaps: "10"
    persistentvolumeclaims: "4"
    replicationcontrollers: "20"
    secrets: "10"
    services: "10"
    services.loadbalancers: "2"
```

## LimitRange

默认情况下，Kubernetes 中所有容器都没有任何 CPU 和内存限制。LimitRange 用来给 Namespace 增加一个资源限制，包括最小、最大和默认资源。比如

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: mylimits
spec:
  limits:
  - max:
      cpu: "2"
      memory: 1Gi
    min:
      cpu: 200m
      memory: 6Mi
    type: Pod
  - default:
      cpu: 300m
      memory: 200Mi
    defaultRequest:
      cpu: 200m
      memory: 100Mi
    max:
      cpu: "2"
      memory: 1Gi
    min:
      cpu: 100m
      memory: 3Mi
    type: Container
```

将 LimitRange 应用于已存在的 Namespace 后，可查看配额默认值与限制：

```bash
kubectl apply -f limitrange.yaml -n <namespace>
kubectl describe limits mylimits -n <namespace>
```

## 配额范围

每个配额在创建时可以指定一系列的范围

| 范围 | 说明 |
| :--- | :--- |
| Terminating | podSpec.ActiveDeadlineSeconds&gt;=0 的 Pod |
| NotTerminating | podSpec.activeDeadlineSeconds=nil 的 Pod |
| BestEffort | 所有容器的 requests 和 limits 都没有设置的 Pod（Best-Effort） |
| NotBestEffort | 与 BestEffort 相反 |

## 原地 Pod 资源调整与配额

原地 Pod 资源调整在 Kubernetes v1.33 达到 Beta、v1.35 达到 GA。资源配额仍应使用受支持的标准资源项（如 `requests.cpu`、`limits.memory`）管理；不要添加 `count/pods.resize`、`count/pods.resize-enabled` 或 `count/pods.resize-active` 等未定义配额键来控制并发 resize。

调整是否成功还取决于 Pod 的 resize policy、节点与容器运行时能力及当前配额。请使用受支持的 Pod resize API，并结合 Pod 状态、事件和 ResourceQuota 的实际用量排错；VPA 或其他自动化控制器的行为需另行验证。
