# API Aggregation

API Aggregation 通过 kube-apiserver 的 aggregation layer 将额外 API group/version 路由到 extension API server。与 CRD 不同，APIService 代理外部 API 服务；适用于需要自定义 API 服务器逻辑、存储或不适合声明式 CRD 的场景。普通声明式资源通常优先使用 CRD。

## Kubernetes v1.37.1 配置要点

* `APIService` 使用稳定 API `apiregistration.k8s.io/v1`，名称格式为 `<version>.<group>`。
* Extension API server 通过 Service 暴露 HTTPS 服务；`APIService.spec.caBundle` 必须信任该服务证书的签发 CA。确保 Service 有可用 Endpoints，且 kube-apiserver 到服务的网络可达。
* 自托管 kube-apiserver 需正确配置 front-proxy/requestheader 证书与信任链；托管集群通常由平台管理这些组件级配置，不要照抄任意控制平面 flags。
* 资源的认证、授权和 admission 仍由 API server / extension API server 各自的配置决定；APIService 不会自动给用户授予权限。

下面的例子演示一个 `example.com/v1` APIService。将 `caBundle` 替换为 extension API server CA 证书 PEM 内容的 base64 编码，并确认服务的 SAN 与 Kubernetes Service DNS 名称匹配。

```yaml
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  name: v1.example.com
spec:
  group: example.com
  version: v1
  groupPriorityMinimum: 1000
  versionPriority: 15
  service:
    namespace: example
    name: example-apiserver
    port: 443
  caBundle: BASE64_ENCODED_CA_CERT
```

```bash
kubectl apply -f apiservice.yaml
kubectl get apiservice v1.example.com
kubectl get --raw /apis/example.com/v1
```

APIService 必须显示 `Available=True`，并能通过 discovery endpoint 返回 API resource list。完整步骤见 [配置 API Aggregation layer](https://kubernetes.io/docs/tasks/extend-kubernetes/configure-aggregation-layer/) 和 [部署 extension API server](https://kubernetes.io/docs/tasks/extend-kubernetes/setup-extension-api-server/)。

## API 服务器开发

API server 与控制器应使用适配目标 Kubernetes 版本的 client-go / apimachinery 依赖和 Go 工具链。可参考上游 [sample-apiserver](https://github.com/kubernetes/sample-apiserver)；不要直接复制旧 apiserver-builder、glide 依赖和已归档 incubator 示例作为当前构建流程。

> 历史说明：早期 Aggregation 配置会在自托管 kube-apiserver 上设置 `--requestheader-*` 与 proxy-client 证书 flags。当前部署必须遵循对应发行版的 aggregation layer 配置指南，正确建立 front-proxy 证书信任链后再注册 APIService；不能只凭一个 Service 和 `APIService` 清单完成安全配置。
