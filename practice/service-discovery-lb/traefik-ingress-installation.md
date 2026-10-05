# Ingress 与入口控制器

Kubernetes Ingress API 声明 HTTP(S) 路由规则；它本身不提供代理，集群必须另行安装与维护 Ingress controller。选择控制器前，核对其当前 release、Kubernetes 支持表、维护状态与安全公告。需要更丰富的流量路由能力时，也可评估 Gateway API 和兼容实现。

> **历史配置不可部署**：本页原有的 Traefik v1 示例依赖已移除的 `extensions/v1beta1` Ingress、RBAC `v1beta1`、早期镜像与 controller 参数。Kubernetes v1.22 已移除旧 Ingress API；不要运行本页原清单。下面只给出当前 `networking.k8s.io/v1` Ingress API 形状，不包含 controller 安装配方。

## Kubernetes v1.37 Ingress 示例

先安装受支持的 Ingress controller，并确认它创建了相应的 `IngressClass`。下面 `public-example`、Service 和 TLS Secret 是占位名称，应用前必须替换为集群中真实资源：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example
  namespace: default
spec:
  ingressClassName: public-example
  tls:
    - hosts:
        - app.example.com
      secretName: example-tls
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: example-service
                port:
                  number: 80
```

Ingress 与后端 Service 必须在同一 namespace。每条 HTTP path 都要声明 `pathType`，后端使用 `service.name` 与 `service.port`。TLS Secret 应只包含所需证书，并按证书管理流程更新。

```bash
kubectl get ingressclass
kubectl describe ingress example
kubectl get ingress,service -n default
```

Controller 专用注解、负载均衡地址、健康检查、TLS 卸载与访问日志均由所选实现决定；使用其对应版本文档，不要从旧 Traefik 参数推断当前行为。

## 参考

- [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Ingress controller](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)
- [Gateway API](https://gateway-api.sigs.k8s.io/)
