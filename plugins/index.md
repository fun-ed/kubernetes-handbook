# Kubernetes插件

Kubernetes在设计之初就充分考虑了[可扩展性](https://kubernetes.io/docs/concepts/overview/extending/)，很多资源或操作都可以通过插件来[自由扩展](https://kubernetes.io/docs/concepts/overview/extending/)，比如认证授权、网络、Volume、容器执行引擎、调度等。

## 面向 Kubernetes v1.37.1

本目录保留的插件资料横跨多个 Kubernetes 版本。部署前先检查相关插件的维护状态、发行版兼容矩阵以及其所依赖的 Kubernetes API；旧配置中的 beta API、旧 CRD schema、旧 Admission 配置或插件端点不能仅通过改版本号继续使用。

容器运行时和 CNI 有独立的当前版本及配置边界，分别见 [CRI 运行时概览](../extension/cri/README.md)和[网络插件概览](../extension/network/README.md)。认证、授权、准入和扩展 API 也应优先按 v1.37 官方文档配置。
