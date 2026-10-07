# Autoscaling

Horizontal Pod Autoscaler（HPA）根据 CPU、内存或已注册的自定义指标调整 Deployment 等可扩缩资源的副本数。

* HPA 控制器定期读取指标，并按比例计算所需副本数。
* Resource 指标由 Metrics API 提供；Pod、Object 和 External 自定义指标需要相应的 metrics API adapter。
* 使用 HPA 前，需要部署与集群版本兼容的 metrics-server。Kubernetes v1.37 的 `metrics.k8s.io/v1` API 已稳定，但 API 后端实际提供的版本取决于所用实现。本书基线 Metrics Server v0.9.0 仅注册并提供 `metrics.k8s.io/v1beta1`，Kubernetes v1.37.1 的 HPA 资源指标客户端也使用 v1beta1；`kubectl top` 可先查询 v1，再回退至 v1beta1。请以集群 API discovery 为准，不要假设后端提供 v1。[Metrics Server v0.9.0 兼容矩阵](https://github.com/kubernetes-sigs/metrics-server/blob/v0.9.0/README.md#compatibility-matrix) · [Kubernetes v1.37.1 HPA client](https://github.com/kubernetes/kubernetes/blob/v1.37.1/pkg/controller/podautoscaler/metrics/client.go)

Node 自动扩展请参考 [Cluster Autoscaler](../../setup/addon-list/cluster-autoscaler.md)。

## API 版本

| API version | 状态 |
| :--- | :--- |
| `autoscaling/v2` | 当前版本，支持 Resource、Pods、Object 和 External metrics |
| `autoscaling/v1` | 仍可用于 CPU 利用率等基本配置，功能有限 |
| `autoscaling/v2beta1`、`autoscaling/v2beta2` | 已移除；分别自 v1.25、v1.26 起不再提供 |
## 示例

```bash
# 创建 Deployment 并配置 CPU request
kubectl create deployment php-apache --image=registry.k8s.io/hpa-example
kubectl set resources deployment/php-apache --requests=cpu=200m
kubectl expose deployment php-apache --port=80

# 创建 HPA
kubectl autoscale deployment php-apache --cpu-percent=50 --min=1 --max=10
kubectl get hpa

# 启动持续请求负载；观察 HPA 副本数变化
kubectl run load-generator --image=busybox:1.37.0 --restart=Never -- \
  sh -c 'while true; do wget -q -O- http://php-apache.default.svc.cluster.local >/dev/null; done'
kubectl get hpa --watch

# 停止负载
kubectl delete pod load-generator
```

使用自定义指标时，集群需要注册并运行兼容的 Custom Metrics 或 External Metrics API adapter。Adapter、指标后端和 HPA 使用的指标名称与单位必须一致。有关 API 聚合与指标适配器，请参考 Kubernetes [metrics 文档](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)及 adapter 项目的版本说明。

下面示例使用 autoscaling/v2，目标 Deployment 需要存在，且各指标 API 必须已由集群提供：

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: php-apache
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-apache
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  - type: Pods
    pods:
      metric:
        name: packets-per-second
      target:
        type: AverageValue
        averageValue: 1k
  - type: Object
    object:
      describedObject:
        apiVersion: networking.k8s.io/v1
        kind: Ingress
        name: main-route
      metric:
        name: requests-per-second
      target:
        type: Value
        value: 10k
```

## 可配置容忍度（Kubernetes v1.37 GA）

HPA 可在 `autoscaling/v2` 的 `behavior.scaleUp.tolerance` 和 `behavior.scaleDown.tolerance` 分别设置扩容与缩容容忍度。此功能在 Kubernetes v1.37 已达到 GA，不需要启用 feature gate。

### 功能概述

默认情况下，HPA 使用 10% 的容忍度。显式配置时，值为 0 到 1 之间的小数，例如 0.05 表示 5%：

### 配置示例

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: configurable-tolerance-example
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 20
  behavior:
    scaleDown:
      tolerance: 0.05  # 5% 容忍度用于缩容
    scaleUp:
      tolerance: 0     # 0% 容忍度用于扩容（更敏感）
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 容忍度使用场景

1. **高敏感度扩容**：设置较低的扩容容忍度，快速响应负载增长
   ```yaml
   behavior:
     scaleUp:
       tolerance: 0.02  # 2% 容忍度，快速扩容
   ```

2. **保守缩容**：设置较高的缩容容忍度，避免频繁缩容
   ```yaml
   behavior:
     scaleDown:
       tolerance: 0.15  # 15% 容忍度，稳定缩容
   ```

3. **不同工作負載的自訂策略**：以下是兩種互相獨立的 `spec.behavior` 片段，請依工作負載擇一設定；不要將兩個片段合併為同一個 `behavior` mapping。

   批次工作負載：積極擴容、保守縮容。
   ```yaml
   behavior:
     scaleUp:
       tolerance: 0
     scaleDown:
       tolerance: 0.2
   ```

   Web 服務：平衡策略。
   ```yaml
   behavior:
     scaleUp:
       tolerance: 0.05
     scaleDown:
       tolerance: 0.1
   ```

- 可配置容忍度在 v1.37 为 GA；常见取值需根据工作负载稳定性和响应速度评估。
- 容忍度较低会使 HPA 对指标变化更敏感；通过监控验证实际扩缩容行为。

## 查看 HPA 状态

使用 `kubectl get hpa` 或 `kubectl describe hpa <name>` 查看当前指标、期望副本数、状态条件和事件。HPA 的详细状态字段见 [HorizontalPodAutoscaler API](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/horizontal-pod-autoscaler-v2/)。

## Vertical Pod Autoscaler（VPA）

VPA 是独立于 Kubernetes 核心仓库的项目，需要安装其 CRD 和控制器；API 字段、更新模式与原地调整的兼容性取决于所安装的 VPA 版本。请以 [VPA 上游文档](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)和对应版本说明为准，不要直接套用旧版 VPA YAML。

Kubernetes 的原地 Pod 资源调整属于核心功能，但它本身不会安装或配置 VPA。HPA 与 VPA 同时控制相同资源时可能互相影响；组合使用前应明确由哪个控制器负责各项资源，并在目标集群上验证行为。
## HPA 最佳实践

* 为容器配置 CPU requests；基于 CPU 利用率的 HPA 需要 requests 才能计算利用率。
* 选择能代表工作负载的指标，并验证 metrics API 与后端的可用性。
* 使用 `kubectl top node` 和 `kubectl top pod` 检查资源指标；这些命令需要正常工作的 metrics-server。
* v1.37 的可配置容忍度已为 GA，可按负载特性设置并监控扩缩容结果。
* 避免让 HPA 与 VPA 同时调整同一资源，除非已针对使用场景验证控制策略。

## 参考文档

* [Ensure High Availability and Uptime With Kubernetes Horizontal Pod Autoscaler and Prometheus](https://www.weave.works/blog/kubernetes-horizontal-pod-autoscaler-and-prometheus)

