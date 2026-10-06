# Kubernetes 证书管理

kubeadm 在初始化集群时管理控制平面证书。自定义 CA、外部 CA、证书轮换和手动生成组件证书都需要按目标 Kubernetes 版本、API endpoint、服务网段与组件身份配置；不要复用带固定旧 IP 的证书主题名称。

为 Kubernetes v1.36/v1.37 自建集群，请从当前 [kubeadm 证书管理文档](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)和所选发行版的 PKI 指南开始。先在隔离环境核对 SAN、信任链、有效期、私钥权限与轮换/恢复流程。不要仅按 `openssl` 或 CFSSL 命令成功就认定证书可用于目标集群。

本仓库旧版 CFSSL 命令和固定地址示例已移入[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/deploy/certificate.md)。它使用旧式 `go get` 安装步骤，且没有针对 Kubernetes v1.36/v1.37 验证，不是当前操作指南。
