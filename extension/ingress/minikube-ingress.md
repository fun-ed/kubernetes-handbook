# Minikube 网络入口

> **旧版实验，不是 Kubernetes v1.37.1 部署指南。** 本页原例依赖 Minikube 的 ingress addon、已归档的 ingress-nginx、旧 `extensions/v1beta1` Ingress schema，以及 `xip.io` 动态 DNS；旧命令和示例输出已移除。

Minikube 中 `Service` 类型 `LoadBalancer` 不会自动创建云厂商负载均衡器。要使用本地 Gateway/Ingress 控制器，应按所选控制器的版本化兼容矩阵部署，并选择受控的本地访问方式（例如 Minikube 支持的 tunnel 或 NodePort）。[Traefik + Gateway API 示例](service-discovery-and-load-balancing.md)固定了 Traefik chart 和与之匹配的 Gateway API CRD 版本；它不会自动为 Minikube 配置外部 DNS 或公网入口。

Minikube addon 与控制器版本由 Minikube 发行版维护；不要假定 `minikube addons enable ingress` 一定安装受支持的控制器。检查实际 addon manifest 和其上游维护状态，避免在新集群启用已归档的 ingress-nginx。

参考：[Minikube 官方文档](https://minikube.sigs.k8s.io/docs/)、[Kubernetes Service LoadBalancer](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer)、[Kubernetes Gateway API](https://gateway-api.sigs.k8s.io/)。
