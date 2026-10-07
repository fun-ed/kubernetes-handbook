# kagent 與 agentgateway：代理模型流量

本章以 kagent 管理 Agent，並讓 agentgateway 代理 LLM 請求。kagent 負責 Agent、ModelConfig 與 MCP 工具的生命週期；agentgateway 負責模型流量入口、上游憑證及路由。兩者是不同服務，不是同一套控制器。範例採用 kagent 官方的 AgentgatewayModel 整合，不使用 standalone 二進位設定，也不混用 agentgateway CRD 與其他 Gateway controller。

## 適用方式與請求路徑

此組合適用於想集中管理模型供應商憑證、觀察模型請求，並讓 kagent Agent 使用 OpenAI-compatible 模型介面的叢集。本章只讓模型請求經過 agentgateway。kagent 內建或另行設定的 MCP 工具連線仍由 kagent 的 `RemoteMCPServer`／`MCPServer` 資源管理；本例不會自動把這些 MCP 請求轉送至 agentgateway，也不會授予 Agent 叢集管理權限。

```text
使用者 → kagent UI/API → kagent Agent → ModelConfig
                                  → agentgateway Gateway → AgentgatewayModel → 模型供應商
                                  → kagent MCP 工具伺服器（獨立流量，不經過本例的模型路由）
```

## 版本與前置需求

版本資料核對日為 **2026-10-07**。手冊的 Kubernetes 基線為 **v1.37.1**，但只有 agentgateway 的官方矩陣明確列出 Kubernetes 1.37；kagent v0.10.3 的發布頁未聲明支援 v1.37，因此尚未確認 kagent 端的官方支援。本章未安裝或實測任何服務。

| 項目 | 固定版本／API | 官方證據與限制 |
| --- | --- | --- |
| Kubernetes | v1.37.1 | 本手冊基線，請參閱[Kubernetes 版本適配指南](../setup/kubernetes-v1.37.md)。 |
| kagent | v0.10.3（穩定版） | [官方 release](https://github.com/kagent-dev/kagent/releases/tag/v0.10.3)。官方 0.x 文件說明 Helm OCI chart 與 `ModelConfig`／`Agent` API；發布資料未說明支援 Kubernetes v1.37。1.0.0-alpha8 是 alpha，不作為本章固定版本。 |
| agentgateway | v1.6.0（穩定版） | [官方 release](https://github.com/agentgateway/agentgateway/releases/tag/v1.6.0) 列出 controller、CRD 與 Helm charts；[相容性矩陣](https://agentgateway.dev/docs/kubernetes/latest/release-notes/versions/)列出 Kubernetes 1.32–1.37、Gateway API 1.4–1.6 及 Helm 3.12 以上。 |
| Gateway API | v1.6.0 Standard CRD | [agentgateway 安裝文件](https://agentgateway.dev/docs/kubernetes/latest/documentation/quickstart/install/)以 v1.6.0 標準 CRD 為例；本例只使用 `Gateway`，不需要 experimental CRD。 |
| agentgateway API | `agentgateway.dev/v1alpha1` | CRD chart `agentgateway-crds` v1.6.0 提供 `AgentgatewayModel` 與 `AgentgatewayParameters`；本例使用這兩個 kind 設定模型路由和生成 Service 的 ClusterIP。v1.6.0 release notes 表示此 API 預設啟用；kagent 官方整合文件仍標示為 experimental，並要求明確設定 `agentgatewayModels.enabled=true`，因此命令明確設定。正式環境啟用前應複核固定版本的 API 狀態。官方[單頁 API 參考](https://agentgateway.dev/docs/kubernetes/latest/reference/api/)亦列出本例未使用的 `AgentgatewayBackend` 與 `AgentgatewayPolicy`。 |
| kagent API | `kagent.dev/v1alpha2` | `ModelConfig` 使用 `kagent.dev/v1alpha2`；固定 v0.10.3 的 `Agent` 同時 served `v1alpha1` 與 `v1alpha2`，本章使用 `v1alpha2` 的 `spec.type: Declarative`／`spec.declarative.modelConfig`。依 [ModelConfig CRD](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent-crds/templates/kagent.dev_modelconfigs.yaml)、[Agent CRD](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent-crds/templates/kagent.dev_agents.yaml) 核對；`RemoteMCPServer` 使用 `kagent.dev/v1alpha2`。 |
| 固定 chart 行為 | agentgateway v1.6.0、kagent v0.10.3 | agentgateway v1.6.0 [Service template](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/pkg/helm/agentgateway/templates/service.yaml) 預設寫入 `type: LoadBalancer`；同版 [AgentgatewayParameters API 型別](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/api/v1alpha1/agentgateway/agentgateway_parameters_types.go) 與 [overlay 型別](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/api/v1alpha1/agentgateway/overlay_types.go) 支援以 `service.spec.type` 覆寫生成 Service。kagent v0.10.3 [values](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/values.yaml)、[Chart template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/Chart-template.yaml) 與 [templates](https://github.com/kagent-dev/kagent/tree/v0.10.3/helm/kagent/templates) 支援本章明列的 RBAC、預設子 chart、ModelConfig 與 UI Route 設定。 |

前置需求：已核准的 Kubernetes v1.37.1 測試叢集、`kubectl`、Helm 3.12 或更新版本、叢集能下載官方映像與 OCI chart，以及可用的 OpenAI API key。先確認目前 context 指向隔離測試叢集。不要在正式環境或使用者既有 context 上直接照抄本章命令。

## 安裝順序

先安裝 Gateway API CRD，再安裝 agentgateway 自有 CRD，最後安裝 controller。CRD 與 controller 固定為相同的 v1.6.0。安裝前應審閱 chart 與 RBAC；下列命令供操作者在隔離叢集執行，本次工作沒有執行這些命令。

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

檢查 API 與 controller：

```bash
kubectl get crd gateways.gateway.networking.k8s.io agentgatewaymodels.agentgateway.dev
kubectl get pods -n agentgateway-system
kubectl get gatewayclass agentgateway
```

預期觀察到相關 CRD 已建立、agentgateway controller Pod 為 `Running`，且 `GatewayClass/agentgateway` 存在並由 controller 管理。這些只是安裝檢查，不代表模型後端已連線或本章已通過執行測試。若升級前已有 CRD，先核對 CRD schema 與所有使用者，不能把 Helm 升級視為可安全回退。

kagent v0.x 官方 Helm 安裝方式分開安裝 CRD 與 controller。固定 v0.10.3 chart 預設啟用 `controller.auth.mode=unsecure`、OpenShift `ui.route.enabled=true`、k8s-agent、kgateway-agent、istio-agent、promql-agent、observability-agent、argo-rollouts-agent、helm-agent、cilium-policy-agent、cilium-manager-agent、cilium-debug-agent、grafana-mcp 與 `kagent-tools`。預設 `rbac.namespaces=[]` 會建立 cluster-scoped 權限並監看所有 namespace。以下 values 將 controller RBAC 限定在 `kagent`，關閉預設管理 Agent、工具伺服器及 MCP 子 chart，停用 UI 對外 Route，並以 `providers: null` 移除預設 provider 設定，避免 chart 建立引用不存在 `kagent-openai` Secret 的預設 ModelConfig。

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

將上述內容存為 `kagent-values.yaml`，再安裝固定版本：

```bash
helm upgrade --install kagent-crds \
  oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds \
  --namespace kagent --create-namespace --version 0.10.3 --wait

helm upgrade --install kagent \
  oci://ghcr.io/kagent-dev/kagent/helm/kagent \
  --namespace kagent --version 0.10.3 \
  --values kagent-values.yaml --wait
```

固定 chart 的 UI Service 預設為 `ClusterIP`；v0.10.3 提供 OpenShift `Route` 與 Gateway API `HTTPRoute`，沒有通用 Ingress template。上述 values 明確關閉兩種 Route，且不建立公網 UI 入口。controller 的 `unsecure` 模式不提供登入認證，只可用於受信任、隔離的測試環境；如需暫時使用 UI，只能綁定 loopback 做 port-forward。正式環境必須設定受支援的身分驗證（例如 `trusted-proxy` 配合已設定好的認證 proxy），並依正式入口設計限制存取。

```bash
kubectl port-forward --address 127.0.0.1 -n kagent svc/kagent-ui 8080:8080
```

這會讓 UI 僅能由執行 port-forward 的本機回環介面連線；請在瀏覽器開啟 `http://127.0.0.1:8080`。kagent chart 的 bundled PostgreSQL 預設供開發／評估使用，不適合作為 production 資料庫。

## 建立模型 Gateway 與憑證

Gateway v1.6.0 controller Helm chart template 會將生成 Service 的 `spec.type` 固定為 `LoadBalancer`。本例使用固定版 `AgentgatewayParameters` 的 Service strategic-merge overlay，將生成 Service 設為 `ClusterIP`。先建立參數物件，再建立 Gateway，避免 controller 先建立預設 LoadBalancer Service。這項設定使 Service 不要求雲端 LoadBalancer；它本身不等同完整的網路隔離，仍須依叢集網路政策限制哪些工作負載可以連線。

先套用完整的 `AgentgatewayParameters`。固定 v1.6.0 CRD 的 `spec.service.spec` 是供生成 Kubernetes Service 使用的 overlay；`Gateway.spec.infrastructure.parametersRef` 會引用同 namespace 的參數物件。

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

建立 Gateway 時，將參數引用放進 `spec.infrastructure`：

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

先透過安全檔案建立上游憑證 Secret。避免將 key 寫在 shell 命令列、YAML、Git、終端記錄或日誌中；不要啟用 shell trace。限制 Secret 的讀取 RBAC。`Authorization` 是 kagent 官方 Agentgateway 整合文件所述的預設 Secret key：

```bash
kubectl create secret generic openai-key -n agentgateway-system \
  --from-file=Authorization=/secure/path/to/openai-api-key
```

`AgentgatewayModel` 的資源名稱就是 kagent 要求的模型名稱。本例依 kagent 官方 Agentgateway 整合欄位建立 `gpt-4o-mini` 模型資源：

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

套用 Gateway 與 AgentgatewayModel 後，檢查 listener、Gateway 狀態及 controller 生成的 Service：

```bash
kubectl apply -f gateway.yaml
kubectl apply -f model.yaml
kubectl get gateway agentgateway-proxy -n agentgateway-system
kubectl get agentgatewaymodel gpt-4o-mini -n agentgateway-system -o yaml
kubectl get svc agentgateway-proxy -n agentgateway-system
test "$(kubectl get svc agentgateway-proxy -n agentgateway-system -o jsonpath='{.spec.type}')" = ClusterIP
```

最後一條命令會在生成的 Service 類型不是 `ClusterIP` 時失敗。預期 Gateway `PROGRAMMED=True`、listener port 為 80，且 Service `type` 為 `ClusterIP`；這只是資源檢查，不證明 Service、模型供應商連線或憑證可用。

## 讓 kagent 使用此模型

kagent 將 agentgateway 視為 OpenAI-compatible provider。URL 必須包含 `/v1`，因為 kagent 會在後面加上 `/chat/completions`。這是叢集內 Service DNS，不是 standalone 設定或外部端點。

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

套用後，先檢查模型設定已被 kagent API 接受：

```bash
kubectl apply -f modelconfig.yaml
kubectl get modelconfig agentgateway-model -n kagent -o yaml
kubectl get agents -n kagent
```

kagent 官方預設管理 Agent 與 MCP 工具已由前述 values 關閉。套用的最小測試 Agent 不宣告任何工具，僅引用 `agentgateway-model`；其 `kagent.dev/v1alpha2`、`type: Declarative` 和欄位結構均來自固定 v0.10.3 中 served 的 Agent CRD schema。

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

在 `http://127.0.0.1:8080` 開啟 `model-path-check`，送出一次非敏感且計費額度受控的請求，並在 agentgateway proxy 日誌／指標確認請求抵達。Agent Ready 或 `ModelConfig` 被接受都不能單獨證明模型請求成功。本例沒有設定 MCP Server，也沒有 MCP tools；模型連線測試不等於 MCP 測試。

kagent 官方另一項所稱「內建 agentgateway 支援」是指 **kmcp** 可為所開發的 MCP 服務提供 agentgateway 整合能力；這不代表本例部署了 MCP route 或工具。若要擴充 MCP，依 [Kubernetes MCP quickstart](https://agentgateway.dev/docs/kubernetes/latest/documentation/quickstart/mcp/)另外建立 MCP backend／HTTPRoute，並只接入已核准的工具及權限。

## 分層驗證

以下是操作者應觀察的訊號，不是本章已執行或已成功的測試結果：

1. **Gateway/controller**：確認 Gateway 的 `Accepted`、`Programmed` conditions，檢查 Service `spec.type` 確為 `ClusterIP`，並查看 proxy Pod 是否就緒。controller Ready 不代表後端可達。
2. **模型連線**：使用無工具的 `model-path-check` Agent 發出一次非敏感、計費額度受控的請求；確認收到模型回應，並在 agentgateway proxy 日誌／指標確認對應路由有請求。不要使用會記錄 Authorization 的除錯模式。
3. **MCP 工具檢查（僅適用於後續自訂／核准 MCP）**：本例未設定 MCP，此項不適用。擴充 MCP 後，才檢查 Agent 工具清單是否僅包含獲准項目，並確認工具來源符合 `RemoteMCPServer`／`MCPServer` 設定。
4. **MCP 工具呼叫（僅適用於後續自訂／核准 MCP）**：本例沒有工具可呼叫。擴充 MCP 後，以唯讀工具問題驗證實際呼叫及輸出；只看到工具清單或模型回覆都不足以證明工具執行成功。

agentgateway UI 與模型入口是不同服務。本例未安裝 agentgateway UI；kagent UI 只可在隔離測試中用 `kubectl port-forward --address 127.0.0.1` 存取，因 controller 使用 `unsecure` 模式。正式環境不可照搬未認證的 UI。

## 故障、升級與回復

- **Gateway 未 programmed 或沒有 Service**：檢查 `GatewayClass` controller name、Gateway conditions、controller events 與日誌；確認 Standard Gateway API v1.6.0 CRD 先於 controller 安裝，且 `AgentgatewayParameters` 已在 Gateway 建立前套用並被 `infrastructure.parametersRef` 引用。
- **生成的 Service 不是 ClusterIP**：確認 Gateway 的 `infrastructure.parametersRef` group、kind、name 與 namespace 正確，並檢查 `AgentgatewayParameters.spec.service.spec.type`。不要用 `kubectl patch` 修正 controller 生成的 Service，因為這不是持久設定。
- **Gateway 已就緒但模型回 404**：檢查 `ModelConfig.openAI.baseUrl` 是否以 `/v1` 結尾、`spec.model` 是否與 `AgentgatewayModel` 名稱完全相同，以及測試 Agent 是否引用該 `ModelConfig`。
- **模型請求 401/403**：檢查 Secret 是否位於 `agentgateway-system`、是否有 `Authorization` key、服務帳號是否能讀取 Secret、供應商 key 是否有效。不要輸出 Secret 內容。kagent chart 的預設 OpenAI ModelConfig 已由 `providers: null` 停用；不要把沒有 Secret 的預設 provider 當成成功。
- **模型請求 5xx／連線失敗**：檢查 proxy DNS/egress、供應商端點、網路政策、TLS 憑證信任、供應商配額及狀態；檢查日誌時過濾憑證與 prompt 等敏感資料。
- **MCP 工具未列舉或無法呼叫**：本例未設定 MCP。只有擴充已核准的 MCP 工具後，才獨立檢查 kagent MCP Server/RemoteMCPServer 狀態、transport URL、網路連線、TLS/auth 與工具名稱。

日常升級時，分別審閱 [kagent release](https://github.com/kagent-dev/kagent/releases) 與 [agentgateway release](https://github.com/agentgateway/agentgateway/releases)、Gateway API 相容性矩陣及 CRD schema。記錄 chart/image 版本與 CRD 變更；先備份 YAML、Secret 的安全副本及 kagent 持久資料，在隔離叢集先升級 CRD 再升級 controller，並重新檢查 API discovery、Gateway conditions、模型及工具呼叫。回復 controller/chart 不會自動回復 CRD schema 或已遷移資料。不要把刪除 CRD 當成正常重裝步驟：刪除某個 CRD 會刪除該 kind 的自訂物件；agentgateway 與 kagent 的 CRD 須分別評估。若必須重建，先確認所有依賴資源已備份且取得核准，再依各專案官方復原文件評估；本章不提供刪除 CRD 的命令。

## 安全邊界

- 本例 agentgateway proxy 使用 HTTP 80 與 `ClusterIP`，只提供叢集內 Service 位址，不建立 LoadBalancer Service。`ClusterIP` 不會替代網路政策、TLS、呼叫者認證與授權。正式環境應依威脅模型設定這些控制項。
- 供應商憑證放在 agentgateway namespace 的 Secret，由 gateway 讀取；kagent Agent 不需保存上游供應商 key。Secret 加密儲存、RBAC、備份及日誌脫敏仍由叢集營運者負責。
- 本章停用預設管理 Agent 與工具，但 controller 權限仍須依固定 chart values 與實際叢集政策審閱。限制 `Gateway`、`AgentgatewayParameters`、`AgentgatewayModel`、`ModelConfig` 與 Agent 的寫入者。
- kagent UI 的 chart Service 為 `ClusterIP` 並關閉 Route／HTTPRoute，但 `controller.auth.mode=unsecure` 不提供認證。僅在受信任隔離測試環境使用，並以 loopback port-forward 存取；production 必須設定認證。
- 將 prompt、工具輸入／輸出與模型回覆視為可能含機密的資料。設定保留、存取及日誌政策，避免在除錯輸出中記錄 Secret、token、個人資料或不必要的 prompt。

## 後續研究：Microsoft Agent Host 與自訂 Harness

本節是截至 **2026-10-07** 的官方資料核對與候選設計，尚未實作或部署，不改變前面的模型路由範例。MCP、A2A 與 AHP 是不同契約；不能把協定發布版本當成固定版 kagent／agentgateway 的互通認證。

### 協定與執行模型

- [Microsoft VS Code Agent Host](https://code.visualstudio.com/blogs/2026/08/26/agent-host-architecture)擁有 agent session，並透過 Agent Host Protocol（AHP）同步多個用戶端。官方 Claude adapter 使用 Anthropic Claude Agent SDK，映射 sessions、tools、permissions 與 subagents。這不是原生 A2A server，也不等於 Microsoft Agent Framework、Azure Foundry Hosted Agents 或 kagent AgentHarness。
- [AHP spec 1.0.0](https://github.com/microsoft/agent-host-protocol/releases/tag/spec/v1.0.0)於 2026-10-02 發布；[changelog](https://github.com/microsoft/agent-host-protocol/blob/main/CHANGELOG.md)中的 1.1.0 尚未發布。協定、語言 SDK 與 VS Code 主程式獨立版本化。AHP MCP channel 的「1.2 release candidate」是[穩定性等級](https://github.com/microsoft/agent-host-protocol/blob/main/docs/specification/versioning.md)，不是 MCP 版本。
- [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/changelog)改為無狀態請求模型；[A2A 1.0](https://a2a-protocol.org/v1.0.0/specification/)的 Agent Card 使用 `supportedInterfaces[]` 宣告各介面的 URL、binding 與協定版本。[kagent BYO 文件](https://kagent.dev/docs/kagent/0.x/examples/a2a-byo.md)中的舊 Card 範例不能證明 A2A 1.0 互通。AHP、Harness SDK 及固定版 gateway 對這些協定版本的支援須另外核對。

### 候選方案比較

| 方案 | 適用方向 | 需要額外處理 |
| --- | --- | --- |
| Claude Agent SDK／自訂 Harness 加 A2A wrapper | 以 headless task workflow 為主 | Card、task、stream、cancel、認證與 session 隔離。本次未確認可直接套用的官方 Claude SDK→A2A adapter。 |
| VS Code Agent Host／AHP | 互動 coding、多用戶端、人工批准與持續 session | 容器執行環境、用戶端依賴、身分驗證；需要 A2A 呼叫時另加 facade。 |
| 自製 AHP-compatible host | 自己管理 Harness 與執行映像 | AHP state、reducers、capability negotiation、批准流程及 workspace 生命週期；任意 image 不會自動註冊為 VS Code host adapter。 |

這是設計比較，不是效能測試。AHP 標準化用戶端工作階段，不規定 Harness 內部如何推理、管理上下文或呼叫工具。

### Kubernetes 與跨 namespace 候選設計

1. namespace A 的 AHP client 經受保護的 WSS 入口連接 namespace B 的 Agent Host。B 按 tenant／workspace 隔離 Harness 與工作目錄，再用 MCP client 呼叫 namespace C 的已核准工具。agentgateway 可列為模型或 MCP 出站入口候選，但需核對具體供應商 API、協定版本與認證，不推定透明相容。
2. 若 kagent／A2A caller 也要呼叫 B，需獨立 A2A facade，把 task／context／message 映射為 AHP session／chat／turn，並處理結果、stream、approval、cancel 與重試冪等。不能直接把 AHP WebSocket 位址當成 A2A endpoint。
3. 跨 namespace Service DNS 不等於授權。分別檢查 caller egress、目標 ingress、DNS、TLS、token audience／scope 與 task／tool owner。直接 DNS 呼叫不需要 `ReferenceGrant`；使用 Gateway API 時，跨 namespace Route attachment 與 backend 引用須遵守[各自規則](https://gateway-api.sigs.k8s.io/guides/multiple-ns/)。

### 部署與驗收邊界

- 官方[獨立 host](https://code.visualstudio.com/docs/agents/concepts/agent-host)命令為 `code agent host`，預設 localhost 並有 connection token。Service 不能讓其他 Pod 直接存取 localhost listener；須依目標版本核對 bind、port、token 與 TLS／proxy 契約，不杜撰 CLI flags。
- 官方[遠端與 Dev Container 工作流程](https://code.visualstudio.com/docs/agents/run/remote-agent-sessions)不證明已有 Kubernetes Helm／operator、相容性矩陣或 SLA；本次未確認這些支援。用戶端重連也不等於 Pod 重啟後復原同一個 live Harness；PVC、Service 與增加 replicas 不會自動提供 HA 或 workspace ownership。
- 候選容器採用 non-root、最小 ServiceAccount、獨立 workspace 與受限 egress；不掛 Docker socket 或 hostPath，無需 API 時不自動掛載 SA token。憑證不得來自個人訂閱登入狀態；依 Harness／供應商正式支援的授權方式設定。
- Host 的基線能力可在用戶端離線時繼續，但用戶端貢獻的工具仍依賴該用戶端。批准者離線時應暫停或拒絕，不自動切換 allow-all。[自動批准不是 OS 安全邊界](https://code.visualstudio.com/docs/agents/run/security)，也不能將 Copilot sandbox 的支援推定涵蓋 Claude／自訂 Harness。
- Host 讀取 `.mcp.json` 與 `~/.copilot/mcp-config.json`；`.vscode/mcp.json` 需要 VS Code 轉送且有互動輸入限制。headless 容器不能假設擁有編輯器的 secrets store 或認證互動。

後續隔離 POC 應分別驗收協定協商、WSS／身分驗證、多用戶端同步與離線批准、Pod replacement、唯讀 MCP 呼叫、A2A task／turn／取消映射、tenant 隔離，以及 image／SDK／服務的授權條款。以上尚未執行，不構成正式環境相容性認證。

## 官方來源

- [kagent 官方 0.x 使用 agentgateway 教學](https://kagent.dev/docs/kagent/0.x/examples/agentgateway/)
- [kagent Agentgateway provider／ModelConfig 範例](https://kagent.dev/docs/kagent/0.x/supported-providers/byo-agentgateway/)
- [kagent v0.10.3 release](https://github.com/kagent-dev/kagent/releases/tag/v0.10.3)
- [kagent 0.x 安裝文件](https://kagent.dev/docs/kagent/0.x/introduction/installation/)
- [kagent MCP 工具指南](https://kagent.dev/docs/kagent/0.x/getting-started/first-mcp-tool/)
- [kmcp 官方內建 agentgateway 支援說明](https://kagent.dev/blog/kmcp)
- [agentgateway Kubernetes MCP quickstart（`AgentgatewayBackend`／HTTPRoute）](https://agentgateway.dev/docs/kubernetes/latest/documentation/quickstart/mcp/)
- [agentgateway v1.6.0 release](https://github.com/agentgateway/agentgateway/releases/tag/v1.6.0)
- [agentgateway Kubernetes 安裝](https://agentgateway.dev/docs/kubernetes/latest/documentation/quickstart/install/)
- [agentgateway Kubernetes 版本支援矩陣](https://agentgateway.dev/docs/kubernetes/latest/release-notes/versions/)
- [agentgateway Kubernetes API 參考](https://agentgateway.dev/docs/kubernetes/latest/reference/api/)
- [agentgateway v1.6.0 controller Helm Service template](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/pkg/helm/agentgateway/templates/service.yaml)
- [agentgateway v1.6.0 AgentgatewayParameters API 型別](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/api/v1alpha1/agentgateway/agentgateway_parameters_types.go) 與 [Kubernetes resource overlay](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/api/v1alpha1/agentgateway/overlay_types.go)
- [kagent v0.10.3 Helm values](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/values.yaml)、[Chart template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/Chart-template.yaml)、[ModelConfig template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/templates/modelconfig.yaml) 與 [UI HTTPRoute template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/templates/ui-httproute.yaml)
- [agentgateway v1.6.0 CRD chart](https://github.com/agentgateway/agentgateway/tree/v1.6.0/controller/install/helm/agentgateway-crds)
- [kagent v0.10.3 ModelConfig Secret template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/templates/modelconfig-secret.yaml)
- [kagent v0.10.3 Agent CRD](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent-crds/templates/kagent.dev_agents.yaml)
- [kagent v0.10.3 UI Service template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/templates/ui-service.yaml) 與 [OpenShift Route template](https://github.com/kagent-dev/kagent/blob/v0.10.3/helm/kagent/templates/openshift-route.yaml)
- [agentgateway v1.6.0 AgentgatewayParameters CRD](https://github.com/agentgateway/agentgateway/blob/v1.6.0/controller/install/helm/agentgateway-crds/templates/agentgateway.dev_agentgatewayparameters.yaml)

- [Gateway API v1.6.0 Standard CRD](https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.0/standard-install.yaml)
