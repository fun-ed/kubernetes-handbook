# Kubernetes 简介

Kubernetes 是谷歌开源的容器集群管理系统，是 Google 多年大规模容器管理技术 Borg 的开源版本，主要功能包括：

* 基于容器的应用部署、维护和滚动升级
* 负载均衡和服务发现
* 跨机器和跨地区的集群调度
* 自动伸缩
* 无状态服务和有状态服务
* 广泛的 Volume 支持
* 插件机制保证扩展性

Kubernetes 发展非常迅速，已经成为容器编排领域的领导者。

## Kubernetes 是一个平台

Kubernetes 提供了很多的功能，它可以简化应用程序的工作流，加快开发速度。通常，一个成功的应用编排系统需要有较强的自动化能力，这也是为什么 Kubernetes 被设计作为构建组件和工具的生态系统平台，以便更轻松地部署、扩展和管理应用程序。

用户可以使用 Label 以自己的方式组织管理资源，还可以使用 Annotation 来自定义资源的描述信息，比如为管理工具提供状态检查等。

此外，Kubernetes 控制器也是构建在跟开发人员和用户使用的相同的 API 之上。用户还可以编写自己的控制器和调度器，也可以通过各种插件机制扩展系统的功能。

这种设计使得可以方便地在 Kubernetes 之上构建各种应用系统。

## Kubernetes 不是什么

Kubernetes 不是一个传统意义上，包罗万象的 PaaS \(平台即服务\) 系统。它给用户预留了选择的自由。

* 不限制支持的应用程序类型，它不插手应用程序框架, 也不限制支持的语言 \(如 Java, Python, Ruby 等\)，只要应用符合 [12 因素](http://12factor.net/) 即可。Kubernetes 旨在支持极其多样化的工作负载，包括无状态、有状态和数据处理工作负载。只要应用可以在容器中运行，那么它就可以很好的在 Kubernetes 上运行。
* 不提供内置的中间件 \(如消息中间件\)、数据处理框架 \(如 Spark\)、数据库 \(如 mysql\) 或集群存储系统 \(如 Ceph\) 等。这些应用直接运行在 Kubernetes 之上。
* 不提供点击即部署的服务市场。
* 不直接部署代码，也不会构建您的应用程序，但您可以在 Kubernetes 之上构建需要的持续集成 \(CI\) 工作流。
* 允许用户选择自己的日志、监控和告警系统。
* 不提供应用程序配置语言或系统 \(如 [jsonnet](https://github.com/google/jsonnet)\)。
* 不提供机器配置、维护、管理或自愈系统。

另外，已经有很多 PaaS 系统运行在 Kubernetes 之上，如 [Openshift](https://github.com/openshift/origin), [Deis](http://deis.io/) 和 [Eldarion](http://eldarion.cloud/) 等。 您也可以构建自己的 PaaS 系统，或者只使用 Kubernetes 管理您的容器应用。

当然了，Kubernetes 不仅仅是一个 “编排系统”，它消除了编排的需要。Kubernetes 通过声明式的 API 和一系列独立、可组合的控制器保证了应用总是在期望的状态，而用户并不需要关心中间状态是如何转换的。这使得整个系统更容易使用，而且更强大、更可靠、更具弹性和可扩展性。

## 核心组件

Kubernetes 集群由控制平面和工作节点组成。控制平面通过 API Server 管理声明式资源；etcd 保存集群状态，controller manager 和 scheduler 推动实际状态接近期望状态。每个工作节点运行 kubelet，并通过 CRI 与容器运行时通信。容器网络由 CNI 插件配置，持久卷由 CSI 驱动提供。

常见的集群网络组件还包括 kube-proxy（除非网络实现自行提供 Service 代理）和 CoreDNS。Kubernetes 不内置通用监控、日志平台或多集群控制平面。metrics-server 等组件由集群发行版或运维人员单独选择和维护。

![](../.gitbook/assets/architecture%20%2810%29.png)

## Kubernetes 版本

本节提供版本参考，不保证每个附加组件都支持表列版本。以下内容以本手册 **Kubernetes v1.37.1 / 2026-10-05 快照**，且 **v1.37 为最新次要版本分支**为前提。Kubernetes 项目维护最新次要版本分支及前两个分支：

| 发布分支 | 此快照中的状态 |
| --- | --- |
| v1.37 | 最新维护中的次要版本分支；本手册基线为 v1.37.1。 |
| v1.36 | 前一个维护中的次要版本分支。 |
| v1.35 | 前两个维护中的次要版本分支。 |

这三个分支不是对未来三个版本的兼容承诺。补丁版本和生命周期日期会变动，请查看[官方 Kubernetes 发布页面](https://kubernetes.io/releases/)确认当前最新补丁和支持状态。Kubernetes 1.19 及更新版本通常获得约一年的补丁支持，具体以官方政策为准。本手册保留旧版本内容，用于说明历史设计和帮助迁移；归档内容或旧示例不是当前部署指南。

### v1.37 API server 的组件版本偏差

下表以**稳态时所有 kube-apiserver 均为 v1.37.x**为基准；HA 升级期间短暂混跑的情况另列于第一行。表中列出上游版本偏差允许范围，不代表建议任意混用补丁版本。请遵循[官方版本偏差策略](https://kubernetes.io/releases/version-skew-policy/)以及部署工具更严格的规则。

| 组件 | 允许的次要版本 |
| --- | --- |
| HA 集群中的 kube-apiserver | 仅在升级过渡期间可混用 v1.36 和 v1.37；各实例间最多相差一个次要版本。 |
| kubelet | v1.34–v1.37。版本不得高于任何 API server。 |
| kube-proxy | v1.34–v1.37，且与同一节点上的 kubelet 最多相差三个次要版本。版本不得高于任何 API server。 |
| kube-controller-manager、kube-scheduler、cloud-controller-manager | v1.36–v1.37；版本不得高于其通信对象中的任何 API server。 |
| kubectl | v1.36–v1.38，比 API server 最多旧或新一个次要版本。此偏差范围不表示 v1.38 已发布。 |

HA 升级期间若 API server 混用不同版本，其他组件的允许范围会缩小：必须逐一符合每个 API server 的版本偏差限制，不能只对照最新版本。升级不得跳过次要版本。v1.34 kubelet 虽在 v1.37 API server 的偏差允许范围内，但这不表示 v1.34 分支仍受官方维护。CNI、CSI 和第三方组件的兼容性须另行核对；Kubernetes 组件版本偏差策略不为它们提供兼容性认证。

本手册基线及各组件的兼容性证据，请参阅 [v1.37.1 适配指南](../setup/kubernetes-v1.37.md)、[组件版本矩阵](../setup/component-versions.md)和[升级指南](../setup/upgrade.md)。

## 参考文档


* [What is Kubernetes?](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)
* [HOW CUSTOMERS ARE REALLY USING KUBERNETES](https://apprenda.com/blog/customers-really-using-kubernetes/)

