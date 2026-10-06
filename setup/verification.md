# 清单验证

验证器用于检查仓库内 `examples/` 和 `manifests/` 的独立 YAML 清单，目标版本为 Kubernetes **v1.37.1**。它不替代[版本适配指南](kubernetes-v1.37.md)中的人工兼容性边界，也不表示所有插件或生产环境均已认证。

## 本地检查

安装 [uv](https://docs.astral.sh/uv/) 后，从仓库根目录运行：

```bash
uv run --script scripts/verify.py
```

需要严格使用已提交依赖锁时运行：

```bash
uv run --locked --script scripts/verify.py
```

脚本 inline metadata 固定 PyYAML 6.0.3 和 jsonschema 4.25.1，并由 `scripts/verify.py.lock` 锁定传递依赖。运行时需联网读取固定提交 `8df8a883b68a24a104b4a9e43c1288090ae60b3b` 中的 Kubernetes v1.37.1 strict standalone JSON schemas。下载、解析或校验失败都会使命令失败，不会静默跳过。该第三方 schema 检查不能代替目标版本 API server 的验证。

本地报告按资源统计 YAML 文件数、排除的历史文件和空文档数、展开 `kind: List` 后的活动资源数、严格 schema 验证通过数、自定义 API 数及错误明细。文件前五行中含有 `# HISTORICAL:` 的清单不计入活动资源。重复 YAML key、解析错误、内置 schema 错误、工作负载 selector 不匹配、空工作负载或 PDB selector，以及旧 seccomp 注解会使命令失败。自定义 API 不会冒充内置 schema 验证通过；报告会单独列出这些资源。

## 当前 Markdown 内嵌 YAML 检查

`scripts/check-current-content.py` 盘点当前章节（包含 `zh-TW/`）中的 YAML 代码围栏，以及 shell/bash 围栏中的 YAML heredoc；并对识别出的内置 Kubernetes API 资源执行 v1.37.1 严格 schema 检查：

```bash
uv run --script scripts/check-current-content.py \
  --output /tmp/kubernetes-current-content.json
```

脚本以 inline metadata 固定 PyYAML 6.0.3 和 jsonschema 4.25.1。输出和 JSON 报告区分内置 served API、自定义 API、kubeadm/kubelet/kube-proxy/k0s/RKE2 原生配置、模板及普通 YAML。邻近文字标记为历史的资源仍执行内置 API schema 检查，不会因警告而略过。自定义 API、原生配置及普通 YAML 只列入清单而不验证 schema；模板不会展开。解析错误、重复键、缺少资源身份或内置 schema 错误会返回失败。该命令仅读取文档和固定上游 schema，不会执行示例、安装组件或操作集群；schema 检查不能代替目标集群验证。

此项检查需要 `go` 可执行文件位于 `PATH` 中。扫描器会调用固定使用 `k8s.io/apiextensions-apiserver` v0.37.1 的辅助程序验证 CRD；这是通过官方程序库进行验证，并不等同于 API Server dry-run 或实际安装。

## 隔离 kind 集群检查

集群模式是显式选择项，不会读取或接受用户 kubeconfig。前置条件：Docker 可用、kind、kubectl 和 uv 已安装；本地已有精确的 v1.37.1 kind node image；运行机可以访问所需 CRD 文件和 `busybox:1.37.0` 镜像。kind v0.33.0 可按[官方 build node image 用法](https://kind.sigs.k8s.io/docs/user/quick-start/#building-images)构建 release image：

```bash
kind build node-image --type release --image local/handbook-k8s-node:v1.37.1 v1.37.1
uv run --locked --script scripts/verify.py \
  --cluster \
  --kind kind \
  --kubectl kubectl \
  --docker docker \
  --image local/handbook-k8s-node:v1.37.1
```

`--image` 必须指向目标 v1.37.1 node image。脚本创建随机命名的独立 kind 集群和权限为当前用户的临时目录；每一条 kubectl 命令都带该目录中的显式 `--kubeconfig`，子进程环境会移除 `KUBECONFIG`。命令行不提供 kubeconfig 参数。创建前会检查随机集群名未被占用；脚本不会复用或修改已有集群。验证结束后，脚本只对 `kind get nodes --name <本次随机集群名>` 返回且名称带该集群前缀的节点执行 `docker stop`。它不会删除集群、容器或卷。私有临时目录保留 kubeconfig 和 JSON 报告，目录路径会写入 stdout 报告。若 kind 创建命令未成功返回，脚本不会停止节点，以免影响无法确认归属的容器。

在任何清单或 CRD 写入前，脚本要求 API server 与每个 kubelet 的完整版本字符串都等于 `v1.37.1`。通过后，它只从上游固定发布文件安装仓库活动自定义 API 所需的 CRD：

- [Gateway API v1.6.2 standard CRDs](https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.2/standard-install.yaml)
- [Gateway API v1.6.2 experimental CRDs](https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.2/experimental-install.yaml)
- [cert-manager v1.21.2 CRDs](https://github.com/cert-manager/cert-manager/releases/download/v1.21.2/cert-manager.crds.yaml)
- [Calico v3.33.0 GlobalNetworkPolicy `projectcalico.org/v3` CRD](https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/api/config/crd/projectcalico.org_globalnetworkpolicies.yaml)

Gateway API 资源使用 `gateway.networking.x-k8s.io` 时，脚本选用 experimental bundle；否则使用 standard bundle。cert-manager 和 Calico 也只在活动清单引用相应 API group 时下载。Calico 目前只安装官方 `GlobalNetworkPolicy` `projectcalico.org/v3` CRD；其他 Calico API（包括旧 `crd.projectcalico.org` group）没有 CRD 源，会在 server dry-run 失败，直到加入对应的精确官方 v3 CRD 文件。脚本检查每份发布文件的所有非空文档，只安全序列化并应用 CRD。Gateway experimental bundle 还包含 `admissionregistration.k8s.io/v1` 的 `ValidatingAdmissionPolicy` 与 `ValidatingAdmissionPolicyBinding`；脚本会确认这两种预期对象存在，将其排除出 apply，并在 `official_bundle_objects_excluded` 报告中记录。其他任何非 CRD 对象都会导致失败关闭。脚本不安装相关控制器或应用，不使用 `--force-conflicts`。它只在这个新建集群内创建清单所需的 Namespace，然后对每个活动独立资源执行 `kubectl apply --dry-run=server --validate=strict`（client-side apply 模式的服务器端 dry-run，避免 SSA 所有权冲突被误判为 schema 错误）。CRD discovery 只对已知的 `paramKind` discovery 错误作有限重试；其他错误直接记入报告并使命令失败。未提供受支持 CRD 的自定义 API 会在 server dry-run 失败，不会被跳过。

所有清单通过后，脚本创建一个最小 BusyBox Deployment 与 Service，并从集群内客户端验证 Service DNS 和 HTTP 响应。该 smoke test 不运行控制器、不测试 client-go informer 事件，也不覆盖持久卷、云服务、Gateway 流量、证书签发、所有附加组件或生产升级。kind 网络与本地镜像拉取前提会影响运行结果；失败会保留在 JSON 报告中。

## 查看历史验证记录

[本次 v1.37.1 适配记录](kubernetes-v1.37.md)包含既有隔离集群测试的范围和结果。该记录是历史证据，不代表本验证器在当前机器上的新运行结果。组件版本和兼容性声明见[组件版本清单](component-versions.md)。

## 本次回归工具验收（2026-10-05）

本节记录新验证器在 2026-10-05 的实际运行，不覆盖上方历史指南的额外控制器测试。该次扫描早于历史文件移入 `archive/`，所列 YAML 文件数、历史排除数与活动资源数描述当时 `examples/` 和 `manifests/` 根目录的内容，不是本次归档后的当前清单数。

* 16 个离线安全／失败路径测试通过，包括重复 YAML key、错误版本、用户 kubeconfig 参数拒绝、CRD-only 提取和 Calico v3 来源检查。
* 本地扫描 97 个 YAML 文件，排除 41 个历史文件；展开后 113 个活动资源，其中 96 个内置资源通过固定提交的 v1.37.1 strict schemas，17 个自定义资源另由 API 检查。
* 新建的独立 kind 集群核实 API server 与全部 kubelet 均为 v1.37.1；113 个资源全部通过严格服务器端 dry-run。
* BusyBox Deployment 就绪、Service DNS 查询和经过 Service 的 HTTP 响应均通过。没有把这个最小 smoke test 称为 informer、Gateway、证书或全组件认证。
* 验证器已停止本次创建的节点容器，检查确认不再运行；没有删除数据。报告与 kubeconfig 留在私有临时目录，不属于仓库或 CI 网站产物。

首次排错发现：Gateway experimental bundle 不只包含 CRD；Calico 存储层的 `crd.projectcalico.org/v1` 清单不是示例的 `projectcalico.org/v3` API；对 kubeadm 已管理的 CoreDNS 使用 SSA dry-run 会产生所有权冲突。这些错误已通过精确来源、严格 CRD 提取和区分 schema 检查与所有权检查修复，并加入对应回归测试，没有忽略失败或使用强制冲突覆盖。
