# Addon-manager 的历史

kube-addon-manager 是早期 Kubernetes 部署（例如旧 `kube-up` 集群）使用的附加组件目录协调器。它不是 kubeadm v1.37.1 的内置组件，也不是新集群通用的 addon 安装工具。本页不提供旧的静态 Pod、旧镜像或 addon-manager YAML 部署命令。

## 历史行为

旧版 addon-manager 用 `addonmanager.kubernetes.io/mode` 标签区分两种目录同步语义：

- `Reconcile`：本地 addon 目录是期望状态；对 API 对象的手动修改会被回滚，删除的对象会重新创建，从目录删除定义才会删除资源。
- `EnsureExists`：目录只保证对象存在；API 修改不会被回滚，但删除的对象会重新创建，移除本地定义也不一定删除已创建资源。

这些语义仅帮助理解旧集群中的对象为什么会被自动覆盖，不代表 Kubernetes 核心 v1.37 中有通用的 add-on manager。原教程引用的 `k8s.gcr.io/kube-addon-manager:v8.7`、Alpha annotations/seccomp 和旧 cluster/addons manifest 已过时，不应应用于新集群。

## 当前集群

使用 kubeadm 时由 kubeadm 管理的控制平面静态 Pod 配置不应通过旧 addon-manager 覆盖。网络、DNS、metrics-server、监控和其他 operator 应按各自当前 upstream release 管理，版本和兼容性见[附加组件列表](README.md)及[组件版本清单](../component-versions.md)。