# 资源控制

本文的 API 示例面向 Kubernetes v1.37.1。资源请求和限制由工作负载作者设定，调度与运行时的具体结果仍取决于节点容量、运行时和准入策略。

## CPU 和内存请求、限制

- `requests` 是调度器放置 Pod 时考虑的资源量；容器在节点上仍可能使用超过 request 的可用资源。
- `limits.cpu` 由内核通过节流执行；`limits.memory` 在节点内存压力下可能导致容器被 OOM kill，并非超限即刻终止。
- 为工作负载设置经过测量的请求和限制，并结合工作负载峰值、节点可用容量及命名空间策略调整，不要仅复制示例数值。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: research
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.29.0
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
```

`nginx:1.29.0` 是示例镜像标签；生产环境应使用组织审查过的镜像，并按供应链策略固定 digest。集群中先创建 `research` namespace，并确保策略允许示例中的镜像。

资源单位、Pod 汇总和额外资源类型（包括 `ephemeral-storage`、HugePages 与 extended resources）详见 [Kubernetes 资源管理文档](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)。

## ResourceQuota 与 LimitRange

配额是 namespace 级上限，不会自动给 Pod 设置合理的资源值。以下示例限制 CPU、内存与 Pod 数量：

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-compute
  namespace: research
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "50"
```

可用 `LimitRange` 为容器指定默认请求/限制或合法范围；它与 ResourceQuota 的作用不同：

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: container-defaults
  namespace: research
spec:
  limits:
  - type: Container
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    default:
      cpu: "500m"
      memory: "512Mi"
```

先按团队工作负载定义额度和默认值，避免默认限制意外压制应用。检查实际生效配置：

```bash
kubectl describe resourcequota -n research
kubectl describe limitrange -n research
kubectl get pods -n research
```

## 原地调整 Pod 资源

原地 Pod CPU/内存资源调整在 Kubernetes v1.35 成为稳定功能。v1.37 可修改运行中 Pod 的容器 `requests` 与 `limits`，不必为了每次变更都重建 Pod；但节点容量不足时调整可能处于 pending/deferred 状态，内存调整也可能依照 `resizePolicy` 重启容器。QoS 类别不会因调整而改变，仍需遵循原有类别的资源规则。请先阅读[官方限制与操作说明](https://kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/)。
原地调整最早在 v1.27 引入，旧章所述的 v1.33 Beta 是历史状态；本章按 v1.35 起稳定的 v1.37 行为说明。

下面的独立 Pod 用于演示 CPU 调整。请求与限制保持相等，便于遵循 Guaranteed QoS 条件：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resize-demo
  namespace: research
spec:
  containers:
  - name: pause
    image: registry.k8s.io/pause:3.10.2
    resizePolicy:
    - resourceName: cpu
      restartPolicy: NotRequired
    - resourceName: memory
      restartPolicy: RestartContainer
    resources:
      requests:
        cpu: "700m"
        memory: "200Mi"
      limits:
        cpu: "700m"
        memory: "200Mi"
```

应用后将 CPU 的 request 和 limit 一起调整；节点必须有足够容量：

```bash
kubectl apply -f resize-demo.yaml
kubectl patch pod resize-demo -n research --subresource resize --type=merge \
  -p '{"spec":{"containers":[{"name":"pause","resources":{"requests":{"cpu":"800m"},"limits":{"cpu":"800m"}}}]}}'
kubectl get pod resize-demo -n research -o yaml
```

查看 Pod conditions 及 `status.containerStatuses[].resources`，确认实际资源已更新。此实验只演示 Kubernetes API；不要把临时修改当作工作负载控制器的期望模板变更。若要持续管理资源，应更新 Deployment/StatefulSet 等控制器的模板并用 rollout 发布。CPU 与内存调整的运行时行为和限制以目标集群文档为准。

## HugePages 与设备资源

HugePages 必须由 Linux 节点预先配置并报告为可分配容量，不能超额分配；`hugepages-<size>` 的请求和限制需匹配节点提供的页大小。参见[HugePages 示例](hugepage.md)和[Kubernetes 操作文档](https://kubernetes.io/docs/tasks/manage-hugepages/scheduling-hugepages/)。

Dynamic Resource Allocation (DRA) 自 Kubernetes v1.34 起 GA，核心 feature gate `DynamicResourceAllocation` 自 v1.35 起锁定启用。DRA 资源需有兼容的设备驱动和集群配置；DeviceClass、ResourceClaim 等对象的字段及可用能力依赖具体驱动，不存在可对所有 GPU/FPGA 驱动通用的假定参数。不要把设备配额、设备污点、自动重新分配或清理策略写成未经驱动/API schema 验证的通用 YAML。按[官方 DRA 概念](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/)及[配置和分配设备的步骤](https://kubernetes.io/docs/tasks/configure-pod-container/assign-resources/)操作。官方文档提示当前调度器不支持 DRA 设备资源的抢占。

GPU 的 NVIDIA Operator、驱动要求和 Kubernetes 支持范围见[GPU 章节](gpu.md)；不要把旧的 `resource.k8s.io/v1alpha2` 示例或未经验证的第三方 ResourceClaim schema 直接应用到集群。

## VPA 与监控工具

Vertical Pod Autoscaler (VPA) 是独立安装的扩展控制器，需先安装与目标 Kubernetes 版本兼容的 VPA release 和 CRD。VPA 的 API、更新模式及其与原地 Pod resize 的集成由 VPA 自身版本决定；Kubernetes 原生 resize 稳定，并不代表任意 VPA manifest 都支持 `InPlace`。按[VPA 上游安装、特性与限制说明](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)选择并验证版本。

`kubectl top` 依赖集群已安装并正常工作的 Metrics API provider；它不是历史命令示例的替代品，也不等同于完整的容量监控。任何额外诊断工具都应核实维护状态、基准版本、镜像、权限和对节点的访问范围后再部署。
