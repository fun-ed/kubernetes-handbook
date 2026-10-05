# Kubernetes Operator

Operator 是组合 Kubernetes API 扩展与控制器协调循环的应用模式。Operator 读取自定义资源（CR），将声明的期望状态与集群/应用实际状态对比，再持续执行创建、配置、升级、备份或恢复操作。

## 资源模型与 reconcile

Operator 通常由以下部分构成：

1. 使用 `apiextensions.k8s.io/v1` CustomResourceDefinition（CRD）声明自定义资源 schema、validation 与版本转换策略。
2. 用户提交 CR；控制器通过 informer/watch 读取相关对象，计算期望状态并幂等地执行变更。
3. 控制器通过 CR 的 `status.conditions` 汇报可观察的进度、错误与恢复状态。
4. 处理删除、升级、重试、凭据、权限、备份恢复和 API 兼容性；避免只实现 happy path。

控制器应拥有完成管理任务所需的最小 RBAC 权限。不要直接给 Operator ServiceAccount 绑定 `cluster-admin`，不要把用户 CR 中的任意字段转成未验证的 shell 命令。CRD 应含必要的 schema、默认值与 CEL validation，并通过 webhook 或新版本的 conversion 管理版本迁移。

## 创建与维护

新项目可使用 [Operator SDK](https://sdk.operatorframework.io/) 或 Kubernetes controller-runtime。按所选工具的稳定 release 安装固定版本，并阅读对应版本的初始化、API 生成、代码生成、测试和部署文档；旧 `make dep`、`git checkout master` 与仓库 `master` 分支命令不构成可复现安装步骤。

发布前至少验证：CRD 安装/升级、controller leader election、权限范围、重试与幂等性、watch 缓存状态、对象删除、集群升级、故障恢复和多实例行为。生产 Operator 的镜像、CRD 与权限应跟随可审计的 release，而非浮动 `latest`。

## 旧 CoreOS etcd-operator 示例（不可部署）

本章原示例安装 `quay.io/coreos/etcd-operator:v0.4.2`，绑定默认 ServiceAccount 与 `cluster-admin`，使用 RBAC `v1alpha1`、`extensions/v1beta1` Deployment、`etcd.coreos.com/v1beta1` 和第三方资源 API。它是早期 Kubernetes/Operator 教程，所有这些 manifest 与 API 不能作为 v1.37 安装示例；旧 `kubectl get thirdpartyresources` 也已失效。不要照抄或应用该示例。

当前扩展资源须使用 `apiextensions.k8s.io/v1` CRD。etcd 集群管理请使用 Kubernetes 发行版或 etcd 项目明确支持的方案，并根据当前 etcd、Kubernetes 与平台文档核对兼容性；不要把旧 CoreOS operator v0.4.2 当作当前推荐工具。

## 参考

- [Kubernetes Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [Kubernetes Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)
- [Operator SDK 文档](https://sdk.operatorframework.io/docs/)
- [OperatorHub](https://operatorhub.io/)
