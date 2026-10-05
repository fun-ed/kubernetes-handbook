# 访问控制

Kubernetes API Server 依次进行认证、授权和准入控制。认证确定请求身份，授权决定该身份能否执行请求；授权通过后，准入控制器才会检查请求。

无论请求来自集群内外，都要遵循 API Server 的认证与授权配置；HTTP 本身不会让请求绕过这些检查。不要通过明文 HTTP 访问 API Server，应使用 TLS，并为客户端配置明确身份和最小权限。

![](../../.gitbook/assets/authentication%20%282%29.png)

## 认证

Kubernetes 为服务账号提供 API 对象，但不直接管理普通用户。客户端请求由 API Server 配置的认证机制处理；无法识别的请求可能作为匿名请求继续处理，具体取决于集群配置。认证失败会返回 HTTP 401。

## 授权

API Server 根据用户、组、请求方法、资源和命名空间等属性判断是否允许请求。请求未获授权时会返回 HTTP 403；只有获准的请求才会进入准入控制阶段。

RBAC 是 Kubernetes 常用的授权机制，本文的 [RBAC 授权](rbac.md)介绍其角色和绑定对象。不要配置允许所有请求的授权方式。

## 参考文档

* [认证](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
* [授权](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)
* [RBAC 授权](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
