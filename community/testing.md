# 单元测试和集成测试

Kubernetes 测试工具与可用目标会随源码分支变化。以下命令以 v1.37.1 源码树为上下文；执行前请查阅该版本的构建脚本以及上游 [SIG Testing 文档](https://github.com/kubernetes/community/tree/master/contributors/devel/sig-testing)。集群级测试不能替代单元测试，单元测试也不能证明特定发行版或 CRI/CNI 实现的行为。

## 单元测试

单元测试验证单个 Go package 的逻辑。修改代码时，应运行受影响 package 的测试并按项目约定添加或更新测试。

```bash
# 在 Kubernetes v1.37.1 源码树中运行一个 package 的测试
make test WHAT=./pkg/api/validation

# 直接使用 Go 工具运行该 package 的测试
go test ./pkg/api/validation

# 只运行名称匹配的测试
go test ./pkg/api/validation -run '^TestValidatePod$'
```

运行整套单元测试可能耗时较长；检查目标、并行度、覆盖率等参数时，以源码树中的测试 Makefile 和开发文档为准，不要假定旧分支的参数在当前分支仍然有效。

## 集成测试

集成测试可能启动本地 API Server、etcd 和其他组件；需要的二进制、资源与环境依赖应按 v1.37.1 测试文档准备。该分支提供的常见入口为：

```bash
make test-integration
```

执行前检查目标的资源占用及清理要求；若只需验证一个 package，优先选择其单元测试，避免无必要地启动完整集成环境。

## 端到端测试

端到端测试需要满足相应集群、平台和权限要求。测试可能创建或删除集群资源，必须使用专用测试环境，并按照上游 [E2E 测试指南](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-testing/e2e-tests.md)及当前分支说明启动和清理测试集群。具体命令、Ginkgo 参数和支持的平台以 v1.37.1 源码树中的文档为准。

Node e2e 与普通集群 e2e 的依赖不同，也需查阅该版本 [Node e2e 测试指南](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-node/e2e-node-tests.md)。不要沿用本页历史的 Federation e2e、GCE 项目变量、旧 `hack/e2e.go` 参数或已过时的 Ginkgo 标志。

## 参考

* [Kubernetes 测试指南](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-testing/testing.md)
* [E2E 测试](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-testing/e2e-tests.md)
* [Node e2e 测试](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-node/e2e-node-tests.md)
* [如何编写 e2e 测试](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-testing/writing-good-e2e-tests.md)
