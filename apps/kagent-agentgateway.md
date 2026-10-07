# kagent 与 agentgateway：代理模型流量

本章以 kagent 管理 agent，并让 agentgateway 代理 LLM 请求。kagent 负责 Agent、ModelConfig 与 MCP 工具的生命周期；agentgateway 负责模型流量入口、上游凭证和路由。它们是两个独立服务，不是同一套控制器。示例采用 kagent 官方的 AgentgatewayModel 集成，不使用 standalone 二进制配置，也不把 agentgateway CRD 与其他 Gateway controller 混用。

## 适用方式与请求路径

此组合适合希望集中管理模型供应商凭证、观察模型请求，并让 kagent Agent 使用 OpenAI-compatible 模型接口的集群。本文只让模型请求经过 agentgateway。kagent 自带或另行配置的 MCP 工具连接仍由 kagent 的 `RemoteMCPServer`／`MCPServer` 资源管理；本例不会把这些 MCP 请求自动转发到 agentgateway，也不会授予 agent 集群管理权限。

```text
用户 → kagent UI/API → kagent Agent → ModelConfig
                                  → agentgateway Gateway → AgentgatewayModel → 模型供应商
                                  → kagent MCP 工具服务器（独立流量，不经过本例的模型路由）
```

## 版本与前提

版本资料核对日为 **2026-10-07**。手册 Kubernetes 基线为 **v1.37.1**，但只有 agentgateway 有官方矩阵明确列出 Kubernetes 1.37；kagent v0.10.3 的发布页没有 v1.37 支持声明，因此该组合的 kagent 端官方支援未确认。本章没有安装或实测任何服务。

| 项目 | 固定版本／API | 官方证据与边界 |
| --- | --- | --- |
| Kubernetes | v1.37.1 | 本手册基线，见[版本适配指南](../setup/kubernetes-v1.37.md)。 |
| kagent | v0.10.3（稳定版） | [官方 release](https://github.com/kagent-dev/kagent/releases/tag/v0.10.3)。官方 0.x 文档说明 Helm OCI chart 与 `ModelConfig`／`Agent` API；发布资料未说明 Kubernetes v1.37 支持。1.0.0-alpha8 是 alpha，不作为本章固定版本。 |
| agentgateway | v1.6.0（稳定版） | [官方 release](https://github.com/agentgateway/agentgateway/releases/tag/v1.6.0) 列出 controller、CRD 与 Helm charts；[兼容矩阵](https://agentgateway.dev/docs/kubernetes/latest/release-notes/versions/)列出 Kubernetes 1.32–1.37、Gateway API 1.4–1.6 和 Helm 3.12+。 |
| Gateway API | v1.6.0 Standard CRDs | [agentgateway 安装文件](https://agentgateway.dev/docs/kubernetes/latest/documentation/quickstart/install/)以 v1.6.0 标准 CRD 为例；这里只用 `Gateway`，不需要 experimental CRD。 |
| agentgateway API | `agentgateway.dev/v1alpha1` | CRD chart `agentgateway-crds` v1.6.0 提供 `AgentgatewayModel` 与 `AgentgatewayParameters`；本例使用这两个 kind，设置模型路由和生成 Service 的 ClusterIP。v1.6.0 release notes 称此 API 默认启用；kagent 官方集成文件仍标为 experimental 并要求显式设 `agentgatewayModels.enabled=true`，因此命令明确设置。生产启用前应复核固定版本的 API 状态。官方[单页 API 参考](https://agentgateway.dev/docs/kubernetes/latest/reference/api/)还列出本例未使用的 `AgentgatewayBackend` 与 `AgentgatewayPolicy`。 |
| kagent API | `kagent.dev/v1alpha2` | `ModelConfig` 使用 `kagent.dev/v1alpha2`；固定 v0.10.3 的 `Agent` 同时 served `v1alpha1` 与 `v1alpha2`，本章使用 `v1alpha2` 的 `spec.type: Declarative`／`spec.declarative.modelConfig`。依 [ModelConfig CRD](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent-crds/templates/kagent.dev_modelconfigs.yaml)、[Agent CRD](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent-crds/templates/kagent.dev_agents.yaml) 核对；`RemoteMCPServer` 使用 `kagent.dev/v1alpha2`。 |
| 固定 chart 行为 | agentgateway v1.6.0、kagent v0.10.3 | agentgateway v1.6.0 [Service template](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/pkg/helm/agentgateway/templates/service.yaml) 默认写入 `type: LoadBalancer`；同版 [AgentgatewayParameters API 类型](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/api/v1alpha1/agentgateway/agentgateway_parameters_types.go) 与 [overlay 类型](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/api/v1alpha1/agentgateway/overlay_types.go) 支持以 `service.spec.type` 覆写生成的 Service。kagent v0.10.3 [values](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/values.yaml)、[Chart template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/Chart-template.yaml) 与 [templates](https://github.com/kagent-dev/kagent/tree/v0.10.3/helm/kagent/templates) 支持本章列出的 RBAC、默认子 chart、ModelConfig 与 UI Route 设置。 |

前置条件：已核准的 Kubernetes v1.37.1 测试集群、`kubectl`、Helm 3.12 或更新版本、可从集群拉取官方镜像与 OCI chart，以及一个可用的 OpenAI API key。先确认当前 context 指向隔离测试集群。不要在生产或使用者既有 context 上照抄本章命令。

## 安装顺序

先安装 Gateway API CRD，再安装 agentgateway 自有 CRD，最后安装 controller。CRD 与 controller 固定为同一 v1.6.0。安装前应审阅 chart 和 RBAC；下列命令是供操作者在隔离集群执行的示例，本次工作没有执行这些命令。

```bash
export GWAPI_VERSION=1.6.0
kubectl apply --server-side -f "https://github.com/kubernetes-sigs/gateway-api/releases/download/v${GWAPI_VERSION}/standard-install.yaml"

helm upgrade --install agentgateway-crds \
  oci://cr.agentgateway.dev/charts/agentgateway-crds \
  --namespace agentgateway-system --create-namespace \
  --version v1.6.0 --wait

helm upgrade --install agentgateway \
  oci://cr.agentgateway.dev/charts/agentgateway \
  --namespace agentgateway-system \
  --version v1.6.0 --set agentgatewayModels.enabled=true --wait
```

检查 API 与 controller：

```bash
kubectl get crd gateways.gateway.networking.k8s.io agentgatewaymodels.agentgateway.dev
kubectl get pods -n agentgateway-system
kubectl get gatewayclass agentgateway
```

预期观察到相关 CRD 已建立，agentgateway controller Pod 为 `Running`，且 `GatewayClass/agentgateway` 存在并由 controller 管理。它们只是安装检查，不代表模型后端已通或本章已通过运行测试。若安装新版本前已存在 CRD，先核对 CRD schema 与所有使用者，不能把 Helm 升级等同于可安全回退。

kagent v0.x 官方 Helm 安装方式分开安装 CRD 与 controller。固定 v0.10.3 chart 默认启用 `controller.auth.mode=unsecure`、OpenShift `ui.route.enabled=true`、k8s-agent、kgateway-agent、istio-agent、promql-agent、observability-agent、argo-rollouts-agent、helm-agent、cilium-policy-agent、cilium-manager-agent、cilium-debug-agent、grafana-mcp 与 `kagent-tools`。默认 `rbac.namespaces=[]` 会创建 cluster-scoped 权限并监看所有 namespace。以下 values 将 controller RBAC 限定在 `kagent`，关闭默认管理 Agent、工具服务器及 MCP 子 chart，停用 UI 对外 Route，并用 `providers: null` 移除默认 provider 设置，避免 chart 创建引用不存在的 `kagent-openai` Secret 的默认 ModelConfig。

```yaml
controller:
  auth:
    mode: unsecure
rbac:
  namespaces:
    - kagent
ui:
  service:
    type: ClusterIP
  route:
    enabled: false
  httpRoute:
    enabled: false
providers: null
kmcp:
  enabled: false
kagent-tools:
  enabled: false
k8s-agent:
  enabled: false
kgateway-agent:
  enabled: false
istio-agent:
  enabled: false
promql-agent:
  enabled: false
observability-agent:
  enabled: false
argo-rollouts-agent:
  enabled: false
helm-agent:
  enabled: false
cilium-policy-agent:
  enabled: false
cilium-manager-agent:
  enabled: false
cilium-debug-agent:
  enabled: false
grafana-mcp:
  enabled: false
oauth2-proxy:
  enabled: false
```

将上述内容存为 `kagent-values.yaml`，再安装固定版本：

```bash
helm upgrade --install kagent-crds \
  oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds \
  --namespace kagent --create-namespace --version 0.10.3 --wait

helm upgrade --install kagent \
  oci://ghcr.io/kagent-dev/kagent/helm/kagent \
  --namespace kagent --version 0.10.3 \
  --values kagent-values.yaml --wait
```

固定 chart 的 UI Service 默认是 `ClusterIP`；v0.10.3 提供 OpenShift `Route` 与 Gateway API `HTTPRoute`，没有通用 Ingress template。上述 values 明确关闭两种 Route，且不建立公网 UI 入口。controller 的 `unsecure` 模式不提供登录认证，只能用于受信任、隔离的测试环境；如需暂时使用 UI，只能绑定 loopback 做 port-forward。生产环境必须设置受支持的身份认证（例如 `trusted-proxy` 配合已设置好的认证 proxy），并按生产入口设计限制访问。

```bash
kubectl port-forward --address 127.0.0.1 -n kagent svc/kagent-ui 8080:8080
```

这会让 UI 只能由执行 port-forward 的本机回环接口访问；请在浏览器打开 `http://127.0.0.1:8080`。kagent chart 的 bundled PostgreSQL 默认供开发／评估使用，不适合作为 production 数据库。

## 建立模型 Gateway 与凭证

Gateway v1.6.0 controller Helm chart template 会将生成 Service 的 `spec.type` 固定为 `LoadBalancer`。本例使用固定版 `AgentgatewayParameters` 的 Service strategic-merge overlay，将生成 Service 设为 `ClusterIP`。先创建参数对象，再创建 Gateway，避免 controller 先创建默认 LoadBalancer Service。这项设置使 Service 不要求云端 LoadBalancer；它本身不代表完整的网络隔离，仍须按集群网络策略限制哪些工作负载可以连接。

先应用完整的 `AgentgatewayParameters`。固定 v1.6.0 CRD 的 `spec.service.spec` 是供生成 Kubernetes Service 使用的 overlay；`Gateway.spec.infrastructure.parametersRef` 会引用同 namespace 的参数对象。

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayParameters
metadata:
  name: agentgateway-internal
  namespace: agentgateway-system
spec:
  service:
    spec:
      type: ClusterIP
```

```bash
kubectl apply -f gateway-parameters.yaml
```

创建 Gateway 时，将参数引用放入 `spec.infrastructure`：

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: agentgateway-proxy
  namespace: agentgateway-system
spec:
  gatewayClassName: agentgateway
  infrastructure:
    parametersRef:
      group: agentgateway.dev
      kind: AgentgatewayParameters
      name: agentgateway-internal
  listeners:
    - name: http
      protocol: HTTP
      port: 80
      allowedRoutes:
        namespaces:
          from: Same
        kinds:
          - group: agentgateway.dev
            kind: AgentgatewayModel
```

先以安全文件建立上游凭证 Secret。避免将 key 写在 shell 命令列、YAML、Git、终端记录或日志中；不要启用 shell trace。限制 Secret 的读取 RBAC。`Authorization` 是 kagent 官方 Agentgateway 集成文件所述的默认 Secret key：

```bash
kubectl create secret generic openai-key -n agentgateway-system \
  --from-file=Authorization=/secure/path/to/openai-api-key
```

`AgentgatewayModel` 的资源名称是 kagent 要求的模型名称。本例依官方 kagent Agentgateway 集成的字段建立 `gpt-4o-mini` 模型资源：

```yaml
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayModel
metadata:
  name: gpt-4o-mini
  namespace: agentgateway-system
spec:
  parentRefs:
    - group: gateway.networking.k8s.io
      kind: Gateway
      name: agentgateway-proxy
      sectionName: http
  provider: OpenAI
  policies:
    auth:
      secretRef:
        name: openai-key
```

应用 Gateway 与 AgentgatewayModel 后，检查 listener、Gateway 状态及 controller 生成的 Service：

```bash
kubectl apply -f gateway.yaml
kubectl apply -f model.yaml
kubectl get gateway agentgateway-proxy -n agentgateway-system
kubectl get agentgatewaymodel gpt-4o-mini -n agentgateway-system -o yaml
kubectl get svc agentgateway-proxy -n agentgateway-system
test "$(kubectl get svc agentgateway-proxy -n agentgateway-system -o jsonpath='{.spec.type}')" = ClusterIP
```

最后一条命令会在生成的 Service 类型不是 `ClusterIP` 时失败。预期 Gateway `PROGRAMMED=True`、listener port 为 80，且 Service `type` 为 `ClusterIP`；这只是资源检查，不证明 Service、模型供应商连线或凭证可用。

## 让 kagent 使用此模型

kagent 将 agentgateway 视为 OpenAI-compatible provider。URL 必须包含 `/v1`，因为 kagent 会在后面加上 `/chat/completions`。这是集群内 Service DNS，不是 standalone 配置或外部端点。

```yaml
apiVersion: kagent.dev/v1alpha2
kind: ModelConfig
metadata:
  name: agentgateway-model
  namespace: kagent
spec:
  provider: OpenAI
  model: gpt-4o-mini
  openAI:
    baseUrl: http://agentgateway-proxy.agentgateway-system.svc.cluster.local/v1
```

套用后，先检查模型设定已被 kagent API 接受：

```bash
kubectl apply -f modelconfig.yaml
kubectl get modelconfig agentgateway-model -n kagent -o yaml
kubectl get agents -n kagent
```

kagent 官方默认管理 Agent 与 MCP 工具已由前述 values 关闭。应用的最小测试 Agent 不声明任何工具，只引用 `agentgateway-model`；其 `kagent.dev/v1alpha2`、`type: Declarative` 和字段结构均来自固定 v0.10.3 中 served 的 Agent CRD schema。

```yaml
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: model-path-check
  namespace: kagent
spec:
  type: Declarative
  declarative:
    modelConfig: agentgateway-model
    systemMessage: "Answer the user's question briefly. Do not claim to use tools."
    tools: []
```

```bash
kubectl apply -f agent.yaml
kubectl get agent model-path-check -n kagent -o yaml
kubectl port-forward --address 127.0.0.1 -n kagent svc/kagent-ui 8080:8080
```

在 `http://127.0.0.1:8080` 打开 `model-path-check`，发送一次非敏感且计费额度受控的请求，并在 agentgateway proxy 日志／指标中确认请求已抵达。Agent Ready 或 `ModelConfig` 被接受都不能单独证明模型请求成功。本例没有配置 MCP Server，也没有 MCP tools；模型连接测试不等于 MCP 测试。

kagent 官方所称的另一项「内建 agentgateway 支持」是指 **kmcp** 可为所开发的 MCP 服务提供 agentgateway 集成能力；这不代表本例部署了 MCP route 或工具。若要扩展 MCP，请依 [Kubernetes MCP quickstart](https://agentgateway.dev/docs/kubernetes/latest/documentation/quickstart/mcp/)另行创建 MCP backend／HTTPRoute，并只接入已核准的工具及权限。

## 分层验证

以下是操作者应观察的信号，不是本章已执行或已成功的测试结果：

1. **Gateway/controller**：确认 Gateway 的 `Accepted`、`Programmed` conditions，检查 Service `spec.type` 确为 `ClusterIP`，并查看 proxy Pod 是否就绪。controller Ready 不代表后端可达。
2. **模型连接**：使用无工具的 `model-path-check` Agent 发出一次非敏感、计费额度受控的请求；确认收到模型响应，并在 agentgateway proxy 日志／指标中确认对应路由有请求。不要使用会记录 Authorization 的调试模式。
3. **MCP 工具检查（仅适用于后续自定义／核准的 MCP）**：本例未配置 MCP，此项不适用。扩展 MCP 后，才检查 Agent 工具清单是否仅包含获准项目，并确认工具来源符合 `RemoteMCPServer`／`MCPServer` 设置。
4. **MCP 工具调用（仅适用于后续自定义／核准的 MCP）**：本例没有工具可调用。扩展 MCP 后，用只读工具问题验证实际调用及输出；只看到工具清单或模型响应都不足以证明工具执行成功。

agentgateway UI 与模型入口是不同服务。本例没有安装 agentgateway UI；kagent UI 只可在隔离测试中用 `kubectl port-forward --address 127.0.0.1` 访问，因为 controller 使用 `unsecure` 模式。生产环境不可照搬未认证的 UI。

## 故障、升级与回退

- **Gateway 未 programmed 或没有 Service**：检查 `GatewayClass` controller name、Gateway conditions、controller events 与日志；确认 Standard Gateway API v1.6.0 CRD 先于 controller 安装，且 `AgentgatewayParameters` 已在 Gateway 创建前应用并由 `infrastructure.parametersRef` 引用。
- **生成的 Service 不是 ClusterIP**：确认 Gateway 的 `infrastructure.parametersRef` group、kind、name 与 namespace 正确，并检查 `AgentgatewayParameters.spec.service.spec.type`。不要用 `kubectl patch` 修改 controller 生成的 Service，因为这不是持久设置。
- **Gateway 已就绪但模型返回 404**：检查 `ModelConfig.openAI.baseUrl` 是否以 `/v1` 结尾、`spec.model` 是否与 `AgentgatewayModel` 名称完全相同，以及测试 Agent 是否引用该 `ModelConfig`。
- **模型请求 401/403**：检查 Secret 是否位于 `agentgateway-system`、是否有 `Authorization` key、服务账号是否能读取 Secret、供应商 key 是否有效。不要输出 Secret 内容。kagent chart 的默认 OpenAI ModelConfig 已由 `providers: null` 停用；不要把没有 Secret 的默认 provider 当成成功。
- **模型请求 5xx／连接失败**：检查 proxy DNS/egress、供应商端点、网络策略、TLS 证书信任、供应商配额及状态；检查日志时过滤凭证与 prompt 等敏感资料。
- **MCP 工具未列举或无法调用**：本例未配置 MCP。只有扩展已核准的 MCP 工具后，才分别检查 kagent MCP Server/RemoteMCPServer 状态、transport URL、网络连接、TLS/auth 与工具名称。

日常升级分别审阅 [kagent release](https://github.com/kagent-dev/kagent/releases) 与 [agentgateway release](https://github.com/agentgateway/agentgateway/releases)、Gateway API 兼容矩阵和 CRD schema。记录 chart/image 版本与 CRD 变更；先备份 YAML、Secret 的安全副本及 kagent 持久资料，在隔离集群升级 CRD 后再升级 controller，并重新检查 API discovery、Gateway conditions、模型和工具调用。回退 controller/chart 不会自动回退 CRD schema 或已迁移资料。不要把删除 CRD 当作正常重装步骤：删除某个 CRD 会删除该 kind 的自定义资源；agentgateway 与 kagent 的 CRD 需分别评估。若必须重建，先确认所有依赖资源已备份且获准，再依各项目官方恢复文件评估；本章不提供删除 CRD 的命令。

## 安全边界

- 本例 agentgateway proxy 使用 HTTP 80 与 `ClusterIP`，只提供集群内 Service 地址，不创建 LoadBalancer Service。`ClusterIP` 不能替代网络策略、TLS、调用者认证与授权。生产环境应按威胁模型配置这些控制项。
- 供应商凭证放在 agentgateway namespace 的 Secret，由 gateway 读取；kagent Agent 不需要保存上游供应商 key。Secret 加密存储、RBAC、备份及日志脱敏仍由集群运营者负责。
- 本章停用默认管理 Agent 与工具，但 controller 权限仍须按固定 chart values 与实际集群策略审阅。限制 `Gateway`、`AgentgatewayParameters`、`AgentgatewayModel`、`ModelConfig` 与 Agent 的写入者。
- kagent UI 的 chart Service 为 `ClusterIP` 并关闭 Route／HTTPRoute，但 `controller.auth.mode=unsecure` 不提供认证。仅在受信任的隔离测试环境使用，并以 loopback port-forward 访问；production 必须配置认证。
- 将 prompt、工具输入／输出与模型响应视为可能含机密的资料。设置保留、访问及日志策略，避免在调试输出中记录 Secret、token、个人资料或不必要的 prompt。

## 后续研究：Microsoft Agent Host 与自定义 Harness

本节是截至 **2026-10-07** 的官方资料核对与候选设计，尚未实现或部署，不改变前面的模型路由示例。MCP、A2A 与 AHP 是不同契约；不能把协议发布版本当成固定版 kagent／agentgateway 的互通认证。

### 协议与执行模型

- [Microsoft VS Code Agent Host](https://code.visualstudio.com/blogs/2026/08/26/agent-host-architecture)拥有 agent session，并通过 Agent Host Protocol（AHP）同步多个客户端。官方 Claude adapter 使用 Anthropic Claude Agent SDK，映射 sessions、tools、permissions 与 subagents。这不是原生 A2A server，也不等于 Microsoft Agent Framework、Azure Foundry Hosted Agents 或 kagent AgentHarness。
- [AHP spec 1.0.0](https://github.com/microsoft/agent-host-protocol/releases/tag/spec/v1.0.0)于 2026-10-02 发布；[changelog](https://github.com/microsoft/agent-host-protocol/blob/main/CHANGELOG.md)中的 1.1.0 尚未发布。协议、语言 SDK 与 VS Code 主程序独立版本化。AHP MCP channel 的「1.2 release candidate」是[稳定性等级](https://github.com/microsoft/agent-host-protocol/blob/main/docs/specification/versioning.md)，不是 MCP 版本。
- [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/changelog)改为无状态请求模型；[A2A 1.0](https://a2a-protocol.org/v1.0.0/specification/)的 Agent Card 使用 `supportedInterfaces[]` 声明各接口的 URL、binding 与协议版本。[kagent BYO 文档](https://kagent.dev/docs/kagent/0.x/examples/a2a-byo.md)中的旧 Card 示例不能证明 A2A 1.0 互通。AHP、Harness SDK 及固定版 gateway 对这些协议版本的支持须另行核对。

### 候选方案比较

| 方案 | 适用方向 | 需要额外处理 |
| --- | --- | --- |
| Claude Agent SDK／自定义 Harness 加 A2A wrapper | 以 headless task workflow 为主 | Card、task、stream、cancel、认证与 session 隔离。本次未确认可直接套用的官方 Claude SDK→A2A adapter。 |
| VS Code Agent Host／AHP | 交互式 coding、多客户端、人工批准与持续 session | 容器执行环境、客户端依赖、身份验证；需要 A2A 调用时另加 facade。 |
| 自制 AHP-compatible host | 自己管理 Harness 与执行镜像 | AHP state、reducers、capability negotiation、批准流程及 workspace 生命周期；任意 image 不会自动注册为 VS Code host adapter。 |

这是设计比较，不是性能测试。AHP 标准化客户端会话，不规定 Harness 内部如何推理、管理上下文或调用工具。

### Kubernetes 与跨 namespace 候选设计

1. namespace A 的 AHP client 经受保护的 WSS 入口连接 namespace B 的 Agent Host。B 按 tenant／workspace 隔离 Harness 与工作目录，再用 MCP client 调用 namespace C 的已核准工具。agentgateway 可列为模型或 MCP 出站入口候选，但需核对具体供应商 API、协议版本与认证，不推定透明兼容。
2. 若 kagent／A2A caller 也要调用 B，需独立 A2A facade，把 task／context／message 映射为 AHP session／chat／turn，并处理结果、stream、approval、cancel 与重试幂等。不能直接把 AHP WebSocket 地址当成 A2A endpoint。
3. 跨 namespace Service DNS 不等于授权。分别检查 caller egress、目标 ingress、DNS、TLS、token audience／scope 与 task／tool owner。直接 DNS 调用不需要 `ReferenceGrant`；使用 Gateway API 时，跨 namespace Route attachment 与 backend 引用须遵守[各自规则](https://gateway-api.sigs.k8s.io/guides/multiple-ns/)。

### 部署与验收边界

- 官方[独立 host](https://code.visualstudio.com/docs/agents/concepts/agent-host)命令为 `code agent host`，默认 localhost 并有 connection token。Service 不能让其他 Pod 直接访问 localhost listener；须按目标版本核对 bind、port、token 与 TLS／proxy 契约，不杜撰 CLI flags。
- 官方[远程与 Dev Container 工作流程](https://code.visualstudio.com/docs/agents/run/remote-agent-sessions)不证明已有 Kubernetes Helm／operator、兼容矩阵或 SLA；本次未确认这些支持。客户端重连也不等于 Pod 重启后恢复同一个 live Harness；PVC、Service 与增加 replicas 不会自动提供 HA 或 workspace ownership。
- 候选容器采用 non-root、最小 ServiceAccount、独立 workspace 与受限 egress；不挂 Docker socket 或 hostPath，无需 API 时不自动挂载 SA token。凭证不得来自个人订阅登录状态；按 Harness／供应商正式支持的授权方式配置。
- Host 的基线能力可在客户端离线时继续，但客户端贡献的工具仍依赖该客户端。批准者离线时应暂停或拒绝，不自动切换 allow-all。[自动批准不是 OS 安全边界](https://code.visualstudio.com/docs/agents/run/security)，也不能将 Copilot sandbox 的支持推定覆盖 Claude／自定义 Harness。
- Host 读取 `.mcp.json` 与 `~/.copilot/mcp-config.json`；`.vscode/mcp.json` 需要 VS Code 转发且有交互输入限制。headless 容器不能假设拥有编辑器的 secrets store 或认证交互。

后续隔离 POC 应分别验收协议协商、WSS／身份验证、多客户端同步与离线批准、Pod replacement、唯读 MCP 调用、A2A task／turn／取消映射、tenant 隔离，以及 image／SDK／服务的授权条款。以上尚未执行，不构成生产兼容性认证。

## 官方来源

- [kagent 官方 0.x 使用 agentgateway 教程](https://kagent.dev/docs/kagent/0.x/examples/agentgateway/)
- [kagent Agentgateway provider／ModelConfig 范例](https://kagent.dev/docs/kagent/0.x/supported-providers/byo-agentgateway/)
- [kagent v0.10.3 release](https://github.com/kagent-dev/kagent/releases/tag/v0.10.3)
- [kagent 0.x 安装说明](https://kagent.dev/docs/kagent/0.x/introduction/installation/)
- [kagent MCP 工具指南](https://kagent.dev/docs/kagent/0.x/getting-started/first-mcp-tool/)
- [kmcp 官方内建 agentgateway 支援说明](https://kagent.dev/blog/kmcp)
- [agentgateway Kubernetes MCP quickstart（`AgentgatewayBackend`／HTTPRoute）](https://agentgateway.dev/docs/kubernetes/latest/documentation/quickstart/mcp/)
- [agentgateway v1.6.0 release](https://github.com/agentgateway/agentgateway/releases/tag/v1.6.0)
- [agentgateway Kubernetes 安装](https://agentgateway.dev/docs/kubernetes/latest/documentation/quickstart/install/)
- [agentgateway Kubernetes 版本支援矩阵](https://agentgateway.dev/docs/kubernetes/latest/release-notes/versions/)
- [agentgateway Kubernetes API 参考](https://agentgateway.dev/docs/kubernetes/latest/reference/api/)
- [agentgateway v1.6.0 controller Helm Service template](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/pkg/helm/agentgateway/templates/service.yaml)
- [agentgateway v1.6.0 AgentgatewayParameters API 型別](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/api/v1alpha1/agentgateway/agentgateway_parameters_types.go) 與 [Kubernetes resource overlay](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/api/v1alpha1/agentgateway/overlay_types.go)
- [kagent v0.10.3 Helm values](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/values.yaml)、[Chart template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/Chart-template.yaml)、[ModelConfig template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/templates/modelconfig.yaml) 與 [UI HTTPRoute template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/templates/ui-httproute.yaml)
- [agentgateway v1.6.0 CRD chart](https://github.com/agentgateway/agentgateway/tree/v1.6.0/controller/install/helm/agentgateway-crds)
- [kagent v0.10.3 ModelConfig Secret template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/templates/modelconfig-secret.yaml)
- [kagent v0.10.3 Agent CRD](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent-crds/templates/kagent.dev_agents.yaml)
- [kagent v0.10.3 UI Service template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/templates/ui-service.yaml) 与 [OpenShift Route template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/templates/openshift-route.yaml)
- [agentgateway v1.6.0 AgentgatewayParameters CRD](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/install/helm/agentgateway-crds/templates/agentgateway.dev_agentgatewayparameters.yaml)

- [Gateway API v1.6.0 Standard CRDs](https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.0/standard-install.yaml)
