# 开发指南

## 开发环境

开发 Kubernetes 时，应以所检出源码版本的构建脚本和开发者文档为准。Kubernetes v1.37.1 要求 Go 至少为 1.26.0；具体 Go 工具链及其他依赖以该版本的 [`build/dependencies.yaml`](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml) 和构建脚本为准。

```bash
git clone https://github.com/kubernetes/kubernetes.git
cd kubernetes
git checkout v1.37.1
```

不要使用本页旧版示例中的 Docker Engine 1.13、Go 1.10、etcd 3.2 或 `apt-key` 安装步骤。Kubernetes 使用 CRI 运行时；开发环境所需工具、构建和本地集群流程可能随源码版本变化，请遵循 [Kubernetes 仓库开发文档](https://github.com/kubernetes/kubernetes/tree/v1.37.1) 与 [Contributor Guide](https://www.kubernetes.dev/docs/)。若要启动本地集群，请先阅读该版本的 `hack/local-up-cluster.sh` 说明，并在隔离的开发环境中执行。

## 测试

单元测试和集成测试的目标、参数及所需工具，应按正在修改的分支文档执行。基础命令和测试范围见[测试指南](testing.md)及上游 [SIG Testing 文档](https://github.com/kubernetes/community/tree/master/contributors/devel/sig-testing)。

修改代码时应一并添加或更新相应测试；端到端测试需要满足对应集群、平台和环境要求，不能将本地单元测试结果视为集群兼容性验证。

## 贡献流程

贡献代码、文档、测试或 issue 处理均可帮助 Kubernetes 社区。开始前请阅读 [Contributor Guide](https://www.kubernetes.dev/docs/)、[代码约定](https://github.com/kubernetes/community/blob/master/contributors/guide/coding-conventions.md)和对应 SIG 的开发指南。Pull Request 应针对明确的问题，附上相应测试说明，并遵循当前仓库的审查与提交要求。

发布分支修复、cherry-pick 及发布经理审批流程会随发布周期变化；不要沿用本文旧版 `release-1.7`、Hub 或过期 Bot 操作示例。请按 [Kubernetes Release SIG](https://github.com/kubernetes/sig-release) 和当前发布分支的贡献指南操作。

## 参考

* [Kubernetes Contributor Community](https://kubernetes.io/community/)
* [Kubernetes Contributor Guide](https://www.kubernetes.dev/docs/)
* [Kubernetes 开发者文档](https://github.com/kubernetes/community/tree/master/contributors/devel)
* [Kubernetes 测试文档](https://github.com/kubernetes/community/tree/master/contributors/devel/sig-testing)
* [Special Interest Groups](https://github.com/kubernetes/community/blob/master/sig-list.md)
* [Kubernetes TestGrid](https://testgrid.k8s.io/)
