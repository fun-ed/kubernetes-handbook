# Istio ambient 模式

本章固定使用 Istio **v1.31.1**。Ambient 模式无需在每个应用 Pod 注入 sidecar，即可提供网格功能。节点上的 ztunnel 处理 L4 连接与 HBONE 通道上的网格 mTLS。可选的 waypoint proxy 基于 Envoy，为选定工作负载处理 L7 功能。Ambient 不会让应用公开，也不能替代 Kubernetes NetworkPolicy、入口网关或 CNI。

Istio ambient CNI 插件会为加入网格的 Pod 设置流量捕获。CNI 安装顺序与 chart 配置很重要，尤其是 Cilium 等其他 CNI 已负责 Pod 网络时。依 v1.31.1 安装说明及 Cilium 集成文档确认 CNI 串接配置。不要让两个插件争用同一责任，也不要假设控制平面安装成功就代表流量捕获正常。

Istio v1.31 支持矩阵包含 Kubernetes v1.32 至 v1.36，不包含本手册基准 v1.37.1。因此本章组合不属于上游声明支持的组合，仅能在隔离实验室评估，不可声称兼容。平台、内核和主机网络限制取决于安装路径，须查阅对应版本的 ambient 要求。

## 安装与命名空间加入

依 [Istio ambient 安装指南](https://istio.io/v1.31/docs/ambient/install/)顺序安装 v1.31.1 base chart、`istiod`、ambient profile/ztunnel 和 CNI 组件。所有 chart 固定为 v1.31.1，并按现有 CNI 核对设置。本章不提供对现有集群执行安装的命令。

控制平面与数据平面已在一次性实验环境部署后，可为测试命名空间添加 ambient 标签：

```bash
kubectl label namespace sample istio.io/dataplane-mode=ambient
```

此标签表示使用 ambient，不是 `istio-injection=enabled`，也不会注入 sidecar。已有 Pod 可能需要重新创建才能加入网格。操作前确认命名空间只含预期工作负载。

## L4 与 waypoint 策略

以下 L4 AuthorizationPolicy 是不使用 waypoint L7 AuthorizationPolicy 时的独立方案。它只允许 `sample` 命名空间的 `frontend` ServiceAccount 连接到标签为 `app: backend`、TCP 8080 的 Pod。

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: backend-l4
  namespace: sample
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - cluster.local/ns/sample/sa/frontend
      to:
        - operation:
            ports: ["8080"]
```

使用 waypoint L7 策略时，不要同时保留上述 L4 策略。经 waypoint 转送后，目的工作负载看到的是 waypoint 身分；只允许原始客户端 ServiceAccount 的 L4 `ALLOW` 策略会阻挡 waypoint。若应用另有 L4 限制，应明确允许 waypoint 身分并在隔离环境验证。

先安装 Istio v1.31 要求的 Gateway API CRD，然后在 `sample` 命名空间建立 waypoint Gateway。以下 Gateway 使用官方支持的 `istio-waypoint` GatewayClass、HBONE listener 15008，并设置 waypoint 处理 Service 流量：

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: sample-waypoint
  namespace: sample
  labels:
    istio.io/waypoint-for: service
spec:
  gatewayClassName: istio-waypoint
  listeners:
    - name: mesh
      port: 15008
      protocol: HBONE
```

Gateway 就绪后，使用 namespace 标签将命名空间内的 Service 流量导向 waypoint：

```bash
kubectl label namespace sample istio.io/use-waypoint=sample-waypoint
```

`istio.io/use-waypoint` 指定 Gateway 名称，不是 `istio-injection=enabled`，也不会注入 sidecar。该标签声明路由意图，不保证 waypoint 不存在或流量类型不匹配时请求失败。若 L7 策略是安全边界，须按 Istio 文档配置强制流量经过 waypoint 的 L4 授权，并验证绕过失败路径。`istio.io/waypoint-for: service` 表示处理 Service 目的流量；若要处理 Pod IP 工作负载流量，须依版本文档设置对应值。

以下 L7 AuthorizationPolicy 通过 `targetRefs` 指向 `sample-waypoint` Gateway，只允许 HTTP GET `/health`。此策略是 waypoint L7 方案，不能与上面只允许客户端 principal 的 L4 策略直接叠加。

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: backend-http
  namespace: sample
spec:
  targetRefs:
    - group: gateway.networking.k8s.io
      kind: Gateway
      name: sample-waypoint
  action: ALLOW
  rules:
    - to:
        - operation:
            methods: ["GET"]
            paths: ["/health"]
```

创建 Gateway 前安装该 Istio 版本要求的 Gateway API CRD。按版本文件检查 GatewayClass 与 Gateway 状态。混合 Istio revision 时，较旧控制平面可能不识别 `targetRefs`，并错误解释策略目标，产生 fail-open 风险。相关 proxy 与控制平面应使用兼容版本；滚动升级前遵循对应版本的防护说明。

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: backend-l4
  namespace: sample
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - cluster.local/ns/sample/sa/frontend
      to:
        - operation:
            ports: ["8080"]
```


## 只读检查与故障排查

```bash
istioctl version
istioctl proxy-status
istioctl ztunnel-config workloads
kubectl get pods -n istio-system -o wide
kubectl get gatewayclass,gateway -A
kubectl get authorizationpolicy -A
```

这些命令检查版本、proxy 同步状态、ztunnel 工作负载及 Gateway/策略资源；它们本身不能证明流量已加密或授权结果正确。使用专用实验工作负载分别测试允许和拒绝的请求。若 ztunnel 未列出工作负载，检查命名空间加入标签、Pod 是否重建、CNI 安装、节点位置及 ztunnel 日志。若 L7 策略未生效，检查 waypoint 就绪状态、use-waypoint 标签、流量是否经过 waypoint、Gateway API 版本及所有相关 revision 是否支持 `targetRefs`。

## 适用边界与回退

未确认 v1.31 文档前，不要让 `hostNetwork` 工作负载或不支持的 runtime/OS 组合加入 ambient。不要将 waypoint 或 Istio 控制平面服务公开到公网。Ambient mTLS 只适用于被网格捕获的流量，不会自动加密所有主机或外部连接。

实验室回退时，先按文档移除或修改命名空间加入标签，再检查流量策略，最后才移除数据平面组件。正式环境须先规划策略迁移、节点覆盖、CNI 串接和控制平面 revision 顺序。卸载 CNI 组件可能中断全部 Pod 网络，不是通用安全回退方法。

主要来源：[Istio v1.31 ambient 概览](https://istio.io/v1.31/docs/ambient/overview/)、[ambient 安装](https://istio.io/v1.31/docs/ambient/install/)、[waypoint](https://istio.io/v1.31/docs/ambient/usage/waypoint/)、[ambient 授权](https://istio.io/v1.31/docs/ambient/usage/l7-features/)、[Istio v1.31.1 发布版本](https://github.com/istio/istio/releases/tag/1.31.1)、[支持状态](https://istio.io/latest/docs/releases/supported-releases/)、[Cilium-Istio 集成](https://docs.cilium.io/en/stable/network/servicemesh/istio/)。
