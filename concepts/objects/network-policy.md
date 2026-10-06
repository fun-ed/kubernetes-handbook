# NetworkPolicy

随着微服务的流行，越来越多的云服务平台需要大量模块之间的网络调用。Kubernetes 在 1.3 引入了 Network Policy，Network Policy 提供了基于策略的网络控制，用于隔离应用并减少攻击面。它使用标签选择器模拟传统的分段网络，并通过策略控制它们之间的流量以及来自外部的流量。

当前 API 为 `networking.k8s.io/v1`。`endPort` 字段自 v1.25 起稳定，不需要启用 feature gate。NetworkPolicy 的执行依赖集群 CNI/数据平面实现支持 NetworkPolicy；创建资源本身不会自动启用隔离。

请使用所选 CNI 厂商当前受维护的部署文档。Calico、Cilium 等实现提供 NetworkPolicy 支持；旧版 Weave Net、Romana 等内容仅作历史参考，不应作为新集群部署指南。

## API 版本

| API version | 状态 |
| :--- | :--- |
| `networking.k8s.io/v1` | 当前版本 |
| `extensions/v1beta1` | 历史 API，自 v1.16 起不再提供 |

## 网络策略

### Namespace 隔离

默认情况下，所有 Pod 之间是全通的。每个 Namespace 可以配置独立的网络策略，来隔离 Pod 之间的流量。

v1.7 + 版本通过创建匹配所有 Pod 的 Network Policy 来作为默认的网络策略，比如默认拒绝所有 Pod 之间 Ingress 通信

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

默认拒绝所有 Pod 之间 Egress 通信的策略为

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes:
  - Egress
```

甚至是默认拒绝所有 Pod 之间 Ingress 和 Egress 通信的策略为

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

而默认允许所有 Pod 之间 Ingress 通信的策略为

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all
spec:
  podSelector: {}
  ingress:
  - {}
```

默认允许所有 Pod 之间 Egress 通信的策略为

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all
spec:
  podSelector: {}
  egress:
  - {}
```

旧版集群曾使用 annotation 配置网络隔离；该方式不属于当前 NetworkPolicy API，不要在 v1.37 集群上依赖它。请使用前述 `networking.k8s.io/v1` 清单。

### Pod 隔离

通过使用标签选择器（包括 namespaceSelector 和 podSelector）来控制 Pod 之间的流量。比如下面的 Network Policy

* 允许 default namespace 中带有 `role=frontend` 标签的 Pod 访问 default namespace 中带有 `role=db` 标签 Pod 的 6379 端口
* 允许带有 `project=myprojects` 标签的 namespace 中所有 Pod 访问 default namespace 中带有 `role=db` 标签 Pod 的 6379 端口

```yaml
# v1.6 以及更老的版本应该使用 extensions/v1beta1
# apiVersion: extensions/v1beta1
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-network-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      role: db
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          project: myproject
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: tcp
      port: 6379
```

另外一个同时开启 Ingress 和 Egress 通信的策略为

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-network-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      role: db
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - ipBlock:
        cidr: 172.17.0.0/16
        except:
        - 172.17.1.0/24
    - namespaceSelector:
        matchLabels:
          project: myproject
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 6379
  egress:
  - to:
    - ipBlock:
        cidr: 10.0.0.0/24
    ports:
    - protocol: TCP
      port: 5978
```

它用来隔离 default namespace 中带有 `role=db` 标签的 Pod：

* 允许 default namespace 中带有 `role=frontend` 标签的 Pod 访问 default namespace 中带有 `role=db` 标签 Pod 的 6379 端口
* 允许带有 `project=myprojects` 标签的 namespace 中所有 Pod 访问 default namespace 中带有 `role=db` 标签 Pod 的 6379 端口
* 允许 default namespace 中带有 `role=db` 标签的 Pod 访问 `10.0.0.0/24` 网段的 TCP 5987 端口

## 简单示例

本例假设集群 CNI 已安装并支持 NetworkPolicy enforcement。NetworkPolicy API 创建成功并不表示流量已经被过滤。

先创建用于测试的 Deployment 和 Service：

```bash
kubectl create deployment nginx --image=nginx:1.30.5 --replicas=2
kubectl expose deployment nginx --port=80
```

以下策略拒绝 default namespace 中所有 Pod 到 nginx Pod 的入站连接；保存为 `default-deny.yaml`：

```yaml
# default-deny.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-nginx
spec:
  podSelector:
    matchLabels:
      app: nginx
  policyTypes:
  - Ingress
```

应用策略后，可启动临时客户端检查访问行为：

```bash
kubectl apply -f default-deny.yaml
kubectl run netcheck --image=busybox:1.37.0 --restart=Never --rm -it -- \
  wget -qO- --timeout=2 http://nginx
```

若只允许带 `access=true` 标签的 Pod 访问 nginx，可将以下策略保存为 `allow-access-nginx.yaml`。该策略与拒绝策略共同生效：

```yaml
# allow-access-nginx.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-access-nginx
spec:
  podSelector:
    matchLabels:
      app: nginx
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          access: "true"
    ports:
    - protocol: TCP
      port: 80
```

分别运行不带标签和带标签的客户端验证 CNI 实际执行结果：

```bash
kubectl apply -f allow-access-nginx.yaml
kubectl run netcheck --image=busybox:1.37.0 --restart=Never --rm -it -- \
  wget -qO- --timeout=2 http://nginx
kubectl run netcheck --image=busybox:1.37.0 --restart=Never --rm -it --labels=access=true -- \
  wget -qO- --timeout=2 http://nginx
```

## 使用场景

### 禁止访问指定服务

```bash
kubectl run web --image=nginx:1.30.5 --labels app=web,env=prod --expose --port 80
```

![](../../.gitbook/assets/15022447799137%20%281%29.jpg)

网络策略

```yaml
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: web-deny-all
spec:
  podSelector:
    matchLabels:
      app: web
      env: prod
```

### 只允许指定 Pod 访问服务

```bash
kubectl run apiserver --image=nginx:1.30.5 --labels app=bookstore,role=api --expose --port 80
```

![](../../.gitbook/assets/15022448622429%20%282%29.jpg)

网络策略

```yaml
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: api-allow
spec:
  podSelector:
    matchLabels:
      app: bookstore
      role: api
  ingress:
  - from:
      - podSelector:
          matchLabels:
            app: bookstore
```

### 禁止 namespace 中所有 Pod 之间的相互访问

![](../../.gitbook/assets/15022451724392%20%283%29.gif)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: default
spec:
  podSelector: {}
```

### 禁止其他 namespace 访问服务

```bash
kubectl create namespace secondary
kubectl run web --namespace secondary --image=nginx:1.30.5 \
    --labels=app=web --expose --port 80
```

![](../../.gitbook/assets/15022452203435%20%281%29.gif)

网络策略

```yaml
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  namespace: secondary
  name: web-deny-other-namespaces
spec:
  podSelector: {}
  ingress:
  - from:
    - podSelector: {}
```

### 只允许指定 namespace 访问服务

```bash
kubectl run web --image=nginx:1.30.5 \
    --labels=app=web --expose --port 80
```

![](../../.gitbook/assets/15022453441751.gif)

网络策略

```yaml
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: web-allow-prod
spec:
  podSelector:
    matchLabels:
      app: web
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          purpose: production
```

### 允许外网访问服务

`LoadBalancer` 可能创建可从集群外访问的负载均衡器并产生费用；仅在确认云平台、入口 ACL/防火墙和工作负载安全设置后使用。NetworkPolicy 不能替代外部防火墙或负载均衡器访问控制。

```bash
kubectl create deployment web --image=nginx:1.30.5
kubectl expose deployment web --type=LoadBalancer --port=80
```

![](../../.gitbook/assets/15022454444461%20%283%29.gif)

网络策略

```yaml
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: web-allow-external
spec:
  podSelector:
    matchLabels:
      app: web
  ingress:
  - ports:
    - port: 80
```

## 不支持场景

- 强制集群内部流量经过某公用网关（这种场景最好通过服务网格或其他代理来实现）；
- 与 TLS 相关的场景（考虑使用服务网格或者 Ingress 控制器）；
- 特定于节点的策略（你可以使用 CIDR 来表达这一需求不过你无法使用节点在 Kubernetes 中的其他标识信息来辩识目标节点）；
- 基于名字来选择服务（不过，你可以使用 标签 来选择目标 Pod 或名字空间，这也通常是一种可靠的替代方案）；
- 创建或管理由第三方来实际完成的“策略请求”；
- 实现适用于所有名字空间或 Pods 的默认策略（某些第三方 Kubernetes 发行版本 或项目可以做到这点）；
- 高级的策略查询或者可达性相关工具；
- 生成网络安全事件日志的能力（例如，被阻塞或接收的连接请求）；
- 显式地拒绝策略的能力（目前，NetworkPolicy 的模型默认采用拒绝操作， 其唯一的能力是添加允许策略）；
- 禁止本地回路或指向宿主的网络流量（Pod 目前无法阻塞 localhost 访问， 它们也无法禁止来自所在节点的访问请求）。

## 参考文档

* [Kubernetes network policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
* [Declare Network Policy](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/)
* [Securing Kubernetes Cluster Networking](https://ahmet.im/blog/kubernetes-network-policy/)
* [Kubernetes Network Policy Recipes](https://github.com/ahmetb/kubernetes-networkpolicy-tutorial)
