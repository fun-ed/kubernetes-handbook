# HTTPS 证书与 ACME（Let's Encrypt）

> **本页旧版安装教程已停用。** 原例使用已归档的 ingress-nginx、Helm `stable` 仓库、`extensions/v1beta1` Ingress、旧 cert-manager annotations 和旧 CRD 安装方式；这些命令和清单不适用于 Kubernetes v1.37.1，不能只改 API 字符串后继续使用。

## Kubernetes v1.37.1 兼容性（2026-10-05）

* ingress-nginx 已于 2026-03-24 归档，维护和安全修复已结束；不要用于新集群。
* 当前 cert-manager 稳定版为 [v1.21.2](https://github.com/cert-manager/cert-manager/releases/tag/v1.21.2)，但其官方支持/测试矩阵只列 Kubernetes 1.33–1.36，没有列出 v1.37。本文不提供在 v1.37.1 上安装该版本的生产命令。
* 新的 HTTPS 入口可评估 [Traefik v3.7.13 + Gateway API Standard v1.6.1](service-discovery-and-load-balancing.md)。Traefik 与 Gateway API 的版本组合必须按该发布版的官方文档固定。

兼容性来源：[cert-manager 支持版本矩阵](https://cert-manager.io/docs/releases/#currently-supported-releases)、[Traefik Gateway API 当前部署示例](service-discovery-and-load-balancing.md)、[Gateway API v1.6.1](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.1)。

## ACME 和 cert-manager 的当前接口

在 cert-manager 明确支持的 Kubernetes 版本上，使用 `cert-manager.io/v1` 的 `Issuer`/`ClusterIssuer`、`Certificate` 和当前 Gateway API solver 配置；不要使用旧的 `certmanager.k8s.io` annotations、`kubernetes.io/tls-acme` 或手动下载旧 CRD 的步骤。

cert-manager 的 Gateway API solver 自 v1.15 起可用。当前官方安装指南使用 OCI Helm chart，Gateway API CRD 应先安装，再配置 controller 的 `config.gatewayAPI.enabled: true`；CRD 变更后，若 cert-manager 已运行，应按文档重启相关 controller。完整配置和示例见 [cert-manager HTTP-01 文档](https://cert-manager.io/docs/configuration/acme/http01/)。

ACME HTTP-01 要求公网 DNS 指向入口地址、TCP 80 能到达 challenge route，并且 Gateway listener 允许 route 所在 namespace。HTTPS 服务还需要让 Gateway 引用同 namespace 中的 TLS Secret。请按实际 Gateway listener 和 cert-manager 支持矩阵验证这些条件；测试时先使用 Let's Encrypt staging endpoint，避免触及生产签发限额。

## 历史示例

旧 NGINX Ingress、Dashboard Basic Auth、`extensions/v1beta1` 后端字段及动态 `master` ClusterIssuer YAML 已移除。Ingress API v1 的字段形状并不足以证明某个旧 Controller、annotation 或 cert-manager 版本兼容 Kubernetes v1.37。
