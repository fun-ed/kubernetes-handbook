# 认证

Kubernetes API 的认证（authentication）将请求映射为用户、UID、组及附加属性，之后由授权器判断是否允许操作。Kubernetes 不提供普通用户对象；用户目录和身份生命周期由外部系统管理。API 请求应使用 TLS，并配置明确的认证方式；不要依赖未加密 HTTP 或匿名访问。

## 常用认证方式

* **X.509 客户端证书**：kube-apiserver 通过 `--client-ca-file` 信任客户端证书；subject 的 CN 映射用户名、O 映射组。证书私钥只能由可信身份管理系统控制，不能把集群 CA 私钥发给用户。
* **ServiceAccount Token**：工作负载身份使用短期、自动轮换的 TokenRequest/projected token。不要把长期 token 写入镜像或自行创建长期 Secret token。ServiceAccount 名称格式为 `system:serviceaccount:<namespace>:<name>`；其组包括 `system:serviceaccounts` 和 `system:serviceaccounts:<namespace>`。
* **Bootstrap Token**：只用于集群引导。自托管 API server 使用 `--enable-bootstrap-token-auth`；controller-manager 需要 `tokencleaner`。kubeadm 会管理相应集群引导流程。不要将 bootstrap token 当作长期用户凭证。
* **OIDC / JWT、Webhook TokenReview、Authenticating Proxy**：根据集群发行版和身份提供商文档配置；验证 issuer、audience、TLS CA 和可信代理请求头来源。
* **静态 Token 文件**：API server 仍支持该机制，但凭据轮换和撤销困难，不适合常规生产身份管理。

Kubernetes v1.37.1 不支持旧文档中的 `--basic-auth-file` 静态密码认证或旧 Keystone 实验性认证 flags。不要部署这些旧配置。完整认证方式、结构化认证配置与匿名访问限制请参考 [Authenticating](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)。

## TokenReview Webhook

Kubernetes v1.37.1 的 `kube-apiserver` 默认以 `authentication.k8s.io/v1beta1` 作为 TokenReview webhook 的 wire version。这个版本选择的是 webhook 请求/响应协议，与 API server 对外提供的 REST API 版本不同。只实现 v1 的 webhook 必须设置 `--authentication-token-webhook-version=v1`；无论选择哪个版本，响应的 API version 和 kind 都必须与请求完全一致。参见 v1.37.1 源码中的[默认值](https://github.com/kubernetes/kubernetes/blob/v1.37.1/pkg/kubeapiserver/options/authentication.go#L237-L242)和[flag 定义](https://github.com/kubernetes/kubernetes/blob/v1.37.1/pkg/kubeapiserver/options/authentication.go#L480-L481)。

Webhook 收到的请求示例：

```json
{
  "apiVersion": "authentication.k8s.io/v1beta1",
  "kind": "TokenReview",
  "spec": {
    "token": "BEARER_TOKEN"
  }
}
```

认证成功时的响应示例：

```json
{
  "apiVersion": "authentication.k8s.io/v1beta1",
  "kind": "TokenReview",
  "status": {
    "authenticated": true,
    "user": {
      "username": "jane@example.com",
      "uid": "user-123",
      "groups": ["developers"]
    }
  }
}
```

Webhook 应验证调用身份、妥善保护 TLS 凭据，并只在验证凭据成功后填充 `status.user`。参考 [Webhook Token Authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#webhook-token-authentication)。

## kubectl exec credential plugin

`exec` credential plugin 是客户端侧扩展。新 kubeconfig 优先使用 `client.authentication.k8s.io/v1`；v1 配置要求明确设置 `interactiveMode`。v1beta1 仍可用于兼容场景；不要使用已移除的 `v1alpha1` ExecCredential API。

```yaml
users:
  - name: example-user
    user:
      exec:
        apiVersion: client.authentication.k8s.io/v1
        command: example-credential-plugin
        interactiveMode: IfAvailable
```

Exec plugin 以本地进程运行，应只使用受信任、可审计的二进制文件。认证 token / client certificate 等凭据应由插件通过 stdout 返回正确版本的 `ExecCredential`，不要把密钥写进 kubeconfig 或日志。参见 [Client-go credential plugins](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#client-go-credential-plugins)。

## 镜像拉取凭据插件

Kubelet credential provider exec 插件用于按需获取镜像仓库凭据，与用户访问 kube-apiserver 的 exec credential plugin 不同。该能力自 Kubernetes v1.26 稳定；使用 Pod ServiceAccount Token 为镜像拉取提供身份是 v1.34 起默认开启的 Beta 功能，配置名为 `KubeletServiceAccountTokenForCredentialProviders`。请依据 kubelet 版本和插件实现配置 `CredentialProviderConfig`，不要使用本文旧的 feature gate 名称或不完整 `tokenAttributes` 配置。参考 [Configure a kubelet image credential provider](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-credential-provider/)。

## 更多资料

* [Authentication reference](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
* [ServiceAccount credentials](https://kubernetes.io/docs/concepts/security/service-accounts/#authenticating-credentials)
* [Managing certificates](https://kubernetes.io/docs/tasks/administer-cluster/certificates/)
