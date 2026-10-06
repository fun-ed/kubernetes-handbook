# CNI 与本地网络实验

CNI（Container Network Interface）定义容器运行时调用网络插件的接口和配置格式；它本身不是完整的 Kubernetes Pod 网络实现。Kubernetes v1.37.1 源码固定 CNI plugins v1.9.1 为依赖版本，但这不代表 Kubernetes 会自动安装网络，也不代表每个 CNI provider 都已获 v1.37 认证。集群必须依据发行版和所选 provider 的版本化文档配置单一主 CNI、IPAM、CIDR、路由与网络策略。

旧版本地实验包含 CNI 0.3.x 示例、namespace/bridge 操作及主机网络变更命令，已移至[归档原始实验](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/extension/network/cni.md)；不要将其用于当前集群。

参考：[Kubernetes 网络模型](https://kubernetes.io/docs/concepts/services-networking/)、[CNI plugins v1.9.1 release](https://github.com/containernetworking/plugins/releases/tag/v1.9.1)、[当前 CNI 版本与限制](README.md)。
