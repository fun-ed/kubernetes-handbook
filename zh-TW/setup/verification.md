# 清單驗證

驗證器用於檢查儲存庫內 `examples/` 和 `manifests/` 的獨立 YAML 清單，目標版本為 Kubernetes **v1.37.1**。它不替代[相容性指南](kubernetes-v1.37.md)中的人工相容性邊界，也不表示所有外掛或生產環境均已認證。

## 本地檢查

安裝 [uv](https://docs.astral.sh/uv/) 後，從儲存庫根目錄執行：

```bash
uv run --script scripts/verify.py
```

需要嚴格使用已提交依賴鎖時執行：

```bash
uv run --locked --script scripts/verify.py
```

指令碼 inline metadata 固定 PyYAML 6.0.3 和 jsonschema 4.25.1，並由 `scripts/verify.py.lock` 鎖定傳遞依賴。執行時需聯網讀取固定提交 `8df8a883b68a24a104b4a9e43c1288090ae60b3b` 中的 Kubernetes v1.37.1 strict standalone JSON schemas。下載、解析或驗證失敗都會使指令失敗，不會靜默跳過。該第三方 schema 檢查不能代替目標版本 API server 的驗證。

本地報告按資源統計 YAML 檔案數、排除的歷史檔案和空文件數、展開 `kind: List` 後的活動資源數、嚴格 schema 驗證通過數、自訂 API 數及錯誤明細。檔案前五行中含有 `# HISTORICAL:` 的清單不計入活動資源。重複 YAML key、解析錯誤、內建 schema 錯誤、工作負載 selector 不匹配、空工作負載或 PDB selector，以及舊 seccomp 註解會使指令失敗。自訂 API 不會冒充內建 schema 驗證通過；報告會單獨列出這些資源。

## 目前 Markdown 內嵌 YAML 檢查

`scripts/check-current-content.py` 盤點目前章節（包含 `zh-TW/`）中的 YAML 程式碼圍欄，以及 shell/bash 圍欄中的 YAML heredoc；並對辨識出的內建 Kubernetes API 資源執行 v1.37.1 嚴格 schema 檢查：

```bash
uv run --script scripts/check-current-content.py \
  --output /tmp/kubernetes-current-content.json
```

指令碼以 inline metadata 固定 PyYAML 6.0.3 和 jsonschema 4.25.1。輸出及 JSON 報告會區分內建 served API、自訂 API、kubeadm/kubelet/kube-proxy/k0s/RKE2 原生設定、範本及一般 YAML。鄰近文字標記為歷史內容的資源仍會執行內建 API schema 檢查，不會因警告而略過。自訂 API、原生設定及一般 YAML 只列入清單，不驗證 schema；範本不會展開。解析錯誤、重複鍵、缺少資源身分或內建 schema 錯誤會回傳失敗。此指令只讀取文件和固定上游 schema，不會執行範例、安裝元件或操作叢集；schema 檢查不能取代目標叢集驗證。

此檢查需要 `PATH` 中有 `go` 可執行檔；掃描器會呼叫固定使用 `k8s.io/apiextensions-apiserver` v0.37.1 的輔助程式檢查 CRD。這只代表透過官方程式庫執行驗證，不等同於 API Server dry-run 或實際安裝。

## 隔離 kind 叢集檢查

叢集模式需明確選用，不會讀取或接受使用者 kubeconfig。前置條件：Docker 可用、kind、kubectl 和 uv 已安裝；本地已有精確的 v1.37.1 kind node image；執行機可以存取所需 CRD 檔案和 `busybox:1.37.0` 映像檔。kind v0.33.0 可按[官方 build node image 用法](https://kind.sigs.k8s.io/docs/user/quick-start/#building-images)建置 release image：

```bash
kind build node-image --type release --image local/handbook-k8s-node:v1.37.1 v1.37.1
uv run --locked --script scripts/verify.py \
  --cluster \
  --kind kind \
  --kubectl kubectl \
  --docker docker \
  --image local/handbook-k8s-node:v1.37.1
```

`--image` 必須指向目標 v1.37.1 node image。指令碼建立隨機命名的獨立 kind 叢集和權限為目前使用者的臨時目錄；每一條 kubectl 指令都帶該目錄中的明確 `--kubeconfig`，子程序環境會移除 `KUBECONFIG`。指令列不提供 kubeconfig 引數。建立前會檢查隨機叢集名稱未被佔用；指令碼不會重複使用或修改已有叢集。驗證結束後，指令碼只對 `kind get nodes --name <本次随机集群名>` 回傳且名稱帶該叢集前綴的節點執行 `docker stop`。它不會刪除叢集、容器或卷。私有臨時目錄保留 kubeconfig 和 JSON 報告，目錄路徑會寫入 stdout 報告。若 kind 建立指令未成功回傳，指令碼不會停止節點，以免影響無法確認歸屬的容器。

在任何清單或 CRD 寫入前，指令碼要求 API server 與每個 kubelet 的完整版本字串都等於 `v1.37.1`。通過後，它只從上游固定發布檔案安裝儲存庫現行自訂 API 所需的 CRD：

- [Gateway API v1.6.2 standard CRDs](https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.2/standard-install.yaml)
- [Gateway API v1.6.2 experimental CRDs](https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.2/experimental-install.yaml)
- [cert-manager v1.21.2 CRDs](https://github.com/cert-manager/cert-manager/releases/download/v1.21.2/cert-manager.crds.yaml)
- [Calico v3.33.0 GlobalNetworkPolicy `projectcalico.org/v3` CRD](https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/api/config/crd/projectcalico.org_globalnetworkpolicies.yaml)

Gateway API 資源使用 `gateway.networking.x-k8s.io` 時，指令碼選用 experimental bundle；否則使用 standard bundle。cert-manager 和 Calico 也只在活動清單引用相應 API group 時下載。Calico 目前只安裝官方 `GlobalNetworkPolicy` `projectcalico.org/v3` CRD；其他 Calico API（包括舊 `crd.projectcalico.org` group）沒有 CRD 來源，會在 server dry-run 失敗，直到加入對應的精確官方 v3 CRD 檔案。指令碼檢查每份發布檔案的所有非空文件，只安全序列化並套用 CRD。Gateway experimental bundle 還包含 `admissionregistration.k8s.io/v1` 的 `ValidatingAdmissionPolicy` 與 `ValidatingAdmissionPolicyBinding`；指令碼會確認這兩種預期物件存在，將其排除出 apply，並在 `official_bundle_objects_excluded` 報告中記錄。遇到任何其他非 CRD 物件時，指令碼都會直接失敗。指令碼不安裝相關控制器或應用，不使用 `--force-conflicts`。它只在這個新建立的叢集內建立清單所需的 Namespace，然後對每個活動獨立資源執行 `kubectl apply --dry-run=server --validate=strict`（client-side apply 模式的伺服器端 dry-run，避免 SSA 所有權衝突被誤判為 schema 錯誤）。CRD discovery 只對已知的 `paramKind` discovery 錯誤作有限重試；其他錯誤直接記入報告並使指令失敗。未提供受支援 CRD 的自訂 API 會在 server dry-run 失敗，不會被跳過。

所有清單通過後，指令碼建立一個最小 BusyBox Deployment 與 Service，並從叢集內客戶端驗證 Service DNS 和 HTTP 回應。該 smoke test 不執行控制器、不測試 client-go informer 事件，也不涵蓋持久卷、雲端服務、Gateway 流量、憑證簽發、所有附加元件或正式環境升級。kind 網路與本地映像檔拉取前提會影響執行結果；失敗會保留在 JSON 報告中。

## 檢視歷史驗證記錄

[本次 v1.37.1 相容性驗證記錄](kubernetes-v1.37.md)包含既有隔離叢集測試的範圍和結果。該記錄是歷史證據，不代表本驗證器在目前機器上的新執行結果。元件版本和相容性宣告見[元件版本清單](component-versions.md)。

## 本次迴歸工具驗收（2026-10-05）

本節記錄新驗證器在 2026-10-05 的實際執行，不涵蓋上方歷史指南中的額外控制器測試。該次掃描早於歷史檔案移入 `archive/`；所列 YAML 檔案數、歷史排除數與活動資源數描述當時 `examples/` 和 `manifests/` 根目錄的內容，不是封存後的目前清單數。

* 16 個離線安全／失敗路徑測試透過，包括重複 YAML key、錯誤版本、使用者 kubeconfig 引數拒絕、CRD-only 提取和 Calico v3 來源檢查。
* 本地掃描 97 個 YAML 檔案，排除 41 個歷史檔案；展開後 113 個活動資源，其中 96 個內建資源通過固定提交的 v1.37.1 strict schemas，17 個自訂資源另由 API 檢查。
* 新建的獨立 kind 叢集核實 API server 與全部 kubelet 均為 v1.37.1；113 個資源全部透過嚴格伺服器端 dry-run。
* BusyBox Deployment 就緒、Service DNS 查詢和經由 Service 的 HTTP 回應均通過。沒有把這個最小 smoke test 稱為 informer、Gateway、憑證或全元件認證。
* 驗證器已停止本次建立的節點容器，檢查確認不再執行；沒有刪除資料。報告與 kubeconfig 留在私有臨時目錄，不屬於儲存庫或 CI 網站產物。

首次排錯發現：Gateway experimental bundle 不只包含 CRD；Calico 儲存層的 `crd.projectcalico.org/v1` 清單不是範例的 `projectcalico.org/v3` API；對 kubeadm 已管理的 CoreDNS 使用 SSA dry-run 會產生所有權衝突。這些錯誤已透過精確來源、嚴格 CRD 提取和區分 schema 檢查與所有權檢查修復，並加入對應迴歸測試，沒有忽略失敗或使用強制衝突覆蓋。
