# kube-apiserver

kube-apiserver 是 Kubernetes 最重要的核心组件之一，主要提供以下的功能

* 提供集群管理的 REST API 接口，包括认证授权、数据校验以及集群状态变更等
* 提供其他模块之间的数据交互和通信的枢纽（其他模块通过 API Server 查询或修改数据，只有 API Server 才直接操作 etcd）

## REST API

kube-apiserver serves the Kubernetes API over HTTPS. The default secure port is 6443. The deprecated insecure HTTP port is not enabled by default and must not be exposed. Use the cluster's authenticated kubeconfig when calling the API.

![img](../../.gitbook/assets/API-server-space%20%282%29.png)

（图片来自 [OpenShift Blog](https://blog.openshift.com/kubernetes-deep-dive-api-server-part-1/)）

在实际使用中，通常通过 [kubectl](https://kubernetes.io/docs/user-guide/kubectl-overview/) 来访问 apiserver，也可以通过 Kubernetes 各个语言的 client 库来访问 apiserver。在使用 kubectl 时，打开调试日志也可以看到每个 API 调用的格式，比如

```bash
$ kubectl --v=8 get pods
```

可通过 `kubectl api-versions` 和 `kubectl api-resources` 查询 Kubernetes API 支持的 API 版本以及资源对象。

## API discovery and OpenAPI

启用的 API 和扩展组件取决于集群配置。使用命令查询当前 API，不要把某个集群导出的 API 版本清单当作其他集群的默认值：

```bash
kubectl api-versions
kubectl api-resources
kubectl api-resources --api-group=storage.k8s.io
kubectl explain deployment.spec
```

kube-apiserver 提供 OpenAPI v3 文档，入口为 `/openapi/v3`。生成客户端代码时，请使用 Kubernetes 客户端生成器当前文档中的流程和目标分支。

## 访问控制

Kubernetes API 的每个请求都会经过多阶段的访问控制之后才会被接受，这包括认证、授权以及准入控制（Admission Control）等。

![](../../.gitbook/assets/access_control%20%283%29.png)

### 认证

开启 TLS 时，所有的请求都需要首先认证。Kubernetes 支持多种认证机制，并支持同时开启多个认证插件（只要有一个认证通过即可）。如果认证成功，则用户的 `username` 会传入授权模块做进一步授权验证；而对于认证失败的请求则返回 HTTP 401。

> **Kubernetes 不直接管理用户**
>
> 虽然 Kubernetes 认证和授权用到了 username，但 Kubernetes 并不直接管理用户，不能创建 `user` 对象，也不存储 username。

更多认证模块的使用方法可以参考 [Kubernetes 认证插件](../../extension/auth/#%20认证)。

### 授权

认证之后的请求就到了授权模块。跟认证类似，Kubernetes 也支持多种授权机制，并支持同时开启多个授权插件（只要有一个验证通过即可）。如果授权成功，则用户的请求会发送到准入控制模块做进一步的请求验证；而对于授权失败的请求则返回 HTTP 403.

更多授权模块的使用方法可以参考 [Kubernetes 授权插件](../../extension/auth/#%20授权)。

### 准入控制

准入控制（Admission Control）用来对请求做进一步的验证或添加默认参数。不同于授权和认证只关心请求的用户和操作，准入控制还处理请求的内容，并且仅对创建、更新、删除或连接（如代理）等有效，而对读操作无效。准入控制也支持同时开启多个插件，它们依次调用，只有全部插件都通过的请求才可以放过进入系统。

更多准入控制模块的使用方法可以参考 [Kubernetes 准入控制](../../extension/auth/admission.md)。

## 部署说明

kube-apiserver 的参数取决于集群部署方式、证书和认证授权配置。请按集群发行版或 kubeadm 当前文档配置控制平面，不要复制旧版本中的 `--insecure-port`、`--admission-control`、`--experimental-bootstrap-token-auth` 或 `--storage-backend` 参数。

## 工作原理

kube-apiserver 提供了 Kubernetes 的 REST API，实现了认证、授权、准入控制等安全校验功能，同时也负责集群状态的存储操作（通过 etcd）。

![](../../.gitbook/assets/kube-apiserver.png)

### 流式列表响应

Kubernetes v1.33 为协商为 JSON 或 Protobuf 的 List 响应增加逐项编码，降低大型资源集合响应时的内存需求。v1.37 将 `StreamingCollectionEncodingToJSON` 和 `StreamingCollectionEncodingToProtobuf` 相关 GA feature gates 移除；不要配置这些门控。具体行为和适用条件请以 [v1.33 发布说明](https://raw.githubusercontent.com/kubernetes/kubernetes/v1.33.0/CHANGELOG/CHANGELOG-1.33.md)及目标版本发布说明为准。该改动不保证每个集群或查询都能获得固定比例的内存节省。

`GET /livez` 用于检查 API Server 是否仍可运行，`GET /readyz` 用于检查是否可以接收流量。程序应检查 HTTP 状态码；运维人员可以用 `kubectl get --raw='/readyz?verbose'` 查看各项检查。

## API 访问

有多种方式可以访问 Kubernetes 提供的 REST API：

* [kubectl](kubectl.md) 命令行工具
* SDK，支持多种语言
  * [Go](https://github.com/kubernetes/client-go)
  * [Python](https://github.com/kubernetes-client/python)
  * [Javascript](https://github.com/kubernetes-client/javascript)
  * [Java](https://github.com/kubernetes-client/java)
  * [CSharp](https://github.com/kubernetes-client/csharp)
  * 其他 [OpenAPI](https://www.openapis.org/) 支持的语言，可以通过 [gen](https://github.com/kubernetes-client/gen) 工具生成相应的 client

### kubectl

```bash
kubectl get --raw /api/v1/namespaces
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods
```
资源指标 API 的版本取决于已注册的后端。本书基线 Metrics Server v0.9.0 注册 `v1beta1.metrics.k8s.io`，未提供 `metrics.k8s.io/v1`；查询前请检查 API discovery。[Metrics Server v0.9.0 API 版本](https://github.com/kubernetes-sigs/metrics-server/blob/v0.9.0/README.md#compatibility-matrix)

### kubectl proxy

`kubectl proxy` uses the credentials in the current kubeconfig and, by default, listens on the local loopback interface:

```bash
kubectl proxy --port=8001
curl http://127.0.0.1:8001/api/
```

不要使用旧示例中的默认 ServiceAccount Secret、`--insecure` 或公开绑定代理地址的方式访问 API。

## API 参考文档

Kubernetes API 参考文档会随当前发行版更新：

* [Kubernetes API Reference](https://kubernetes.io/docs/reference/kubernetes-api/)
* [API deprecation guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)
