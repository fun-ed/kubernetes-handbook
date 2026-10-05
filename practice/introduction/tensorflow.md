# 在 Kubernetes 上运行 TensorFlow

原章节基于早期 Kubeflow、ksonnet 0.8、`ks` 命令、旧 `gcr.io/kubeflow/*` Notebook 镜像和未经限制的 `cluster-admin` 绑定。该流程不是 Kubernetes v1.37 的 Kubeflow 安装方式；旧的管理员绑定、任意用户名/密码登录和 `ks generate` 命令不能作为当前操作示例，已移除。

当前 Kubeflow 可按需安装独立子项目，或使用 Kubeflow Community Distribution / 由维护者提供的发行版。各发行版、Notebook、Trainer、Pipelines 与模型服务组件分别维护版本和 Kubernetes 支持范围；在 Kubernetes v1.37.1 集群部署前，应核实所选发行版及组件的兼容矩阵和安全升级路径，而不要把一个组件的版本套用到整个平台。[Kubeflow 安装选项](https://www.kubeflow.org/docs/started/installing-kubeflow/)

## 工作负载选择

- Notebook：按当前 [Kubeflow Notebooks 文档](https://www.kubeflow.org/docs/components/notebooks/)部署，并配置组织认可的身份认证、授权、网络访问和资源配额；不要公开未认证的 Notebook 服务。
- 分布式训练：选择当前维护的训练控制器或 [Kubeflow Trainer](https://www.kubeflow.org/docs/components/trainer/)，并针对所选框架和 Kubernetes 版本审查 CRD、Operator 与运行时要求。
- GPU：在部署训练工作负载前，先确认节点驱动、CRI、GPU Operator/Device Plugin 或 DRA 驱动的支持范围，见[本手册 GPU 章节](../gpu.md)。
- 模型服务：单独核实当前服务组件的 API、认证与 Kubernetes 支持范围，不再使用旧 `ks generate tf-serving` 示例。

容器镜像应包含与训练任务匹配的 TensorFlow、Python/CUDA 和应用依赖；将镜像发布到集群可访问的 registry，并按供应链策略固定 digest。为每个控制器和工作负载设置最小权限的 ServiceAccount、CPU/内存/GPU 资源以及适当的 Pod 安全策略。具体 API 和安装步骤以所选项目的官方版本文档为准。

参考：[TensorFlow 官方文档](https://www.tensorflow.org/)、[Kubeflow 子项目文档](https://www.kubeflow.org/docs/components/)。
