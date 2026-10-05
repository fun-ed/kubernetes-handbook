---
name: skill-debug
description: 重現或診斷本倉庫的 Kubernetes v1.37 範例、manifest、Go/Python 程式或 GitBook 工具鏈故障時使用。先核對精確目標與可重現證據，再用最小修改驗證根因。
---

# 除錯 SOP

## 觸發與前提

發生 manifest 套用失敗、API/schema 錯誤、控制器或 informer 異常、範例程式失敗、文件產生問題或工具鏈錯誤時使用。先讀 [AGENTS.md](../AGENTS.md)、[Kubernetes v1.37 指南](../setup/kubernetes-v1.37.md)及[清單狀態說明](../manifests/README.md)。以使用者指定的 Kubernetes、元件、架構、檔案、context、命令和輸出為準。叢集操作只在明確指定的 disposable/test context 執行；每個 `kubectl` 命令明寫 `--context`，不使用 default 或 production context。

## 步驟

1. **先鎖定重現條件。** 保存失敗命令、退出碼、完整錯誤、檔案/行號、程式版本、目標映像 tag/digest、CPU 架構、Kubernetes 版本、context 類型和執行時間。遮蔽 token、kubeconfig 內容、私人 URL 與個資。沒有這些證據時先標為未知，不先猜根因。
2. **縮小到單一失敗面。** 從錯誤所在層開始：YAML/parser、API discovery/schema、admission、控制器/服務、程式生命週期、runtime/dependency、GitBook/plugin。逐步移除無關資源或功能，使用可重現的最小檔案/測試命令。只改一個假設；記錄原始結果與修改後結果。
3. **先查目標版本的正式契約。** 對 Kubernetes API 查該版本 served APIs/schema；對外掛查精確 release tag 文件，而不是把 live docs 或最新版範例當成舊版本事實。區分 CRD 是否已註冊、controller 是否啟動及該 controller 是否支援該 API/feature。
4. **用安全方式重現。** YAML 與 API 問題先對一個已檢查的檔案做 client/server dry-run。Server dry-run 僅在 CRD、webhook 和 API 已就緒的 disposable/test cluster 有效；dry-run 成功不證明 DNS、資料面、卷或業務流程成功。

   ```bash
   # 前提：KUBECONFIG 與 context 已明確指向 disposable/test cluster；FILE 是單一人工審查過的檔案。
   : "${KUBECONFIG:?設定測試 kubeconfig 路徑}"
   : "${KUBE_CONTEXT:?設定精確的測試 context}"
   : "${FILE:?設定單一已審查的 manifest 路徑}"
   kubectl --kubeconfig "$KUBECONFIG" --context "$KUBE_CONTEXT" \
     apply --dry-run=server --validate=strict -f "$FILE"
   ```

5. **套用最小修正並重跑同一重現。** 保留最小可理解 diff，另做回歸檢查，並確認歷史檔案、測試 fixture、產生檔與生產安全設定沒有被順帶改動。若重現需要叢集寫入，先確認 disposable 資源歸屬與清理界線。
6. **如實分類結果。** `已重現` 是有相同目標條件與輸出的現象；`已修復` 需同一條件下錯誤消失且相關回歸檢查通過；`受阻` 是已找到明確外部相依或工具鏈限制、修正範圍超出任務；`未知` 是證據仍不足或尚未做相應檢查。停止、跳過或未執行的步驟不可寫成通過。

## 已知故障線索

| 現象 | 先核對與處理 | 限制 |
| --- | --- | --- |
| Traefik Gateway provider 拒絕 80/443 listener，Traefik entryPoints 卻設為 8000/8443 | 讀取精確 tag 的 Gateway provider 文件及 controller status/conditions；核對 `Gateway.spec.listeners[].port`、Traefik entryPoints、Pod `containerPort` 和 Service `port`/`targetPort` 映射。此範例曾因 entryPoints 8000/8443 而拒絕 Gateway 80/443；修正將 entryPoints、containerPort、Service targetPort 設為 80/443，並在 Kubernetes v1.37.1 通過有限的 HTTP/HTTPS smoke test。Service 的 port 到 targetPort 映射不代表 Gateway controller 接受該 listener port，須依 controller 契約判定。 | Traefik v3.7.13 尚無 Kubernetes v1.37 官方支援聲明；smoke test 不構成上游相容認證。沒有外部 LoadBalancer 時，不能由 manifest 或叢集內測試推論外部連線正常。 |
| 大型 CRD 出現 annotations 超過 262144 bytes | 確認錯誤指向 `metadata.annotations` 而非 CRD schema/body 本身。檢查是否用 client-side apply 寫入龐大的 `kubectl.kubernetes.io/last-applied-configuration`；對測試環境先用 strict server-side dry-run 和明確 field manager，再評估 server-side apply。 | 不要直接刪掉 live annotation 或覆寫其他 manager 的欄位；先檢查 ownership/conflict。SSA 不會修復真正超大的單一 annotation 或無效 CRD schema。 |
| Calico v3.33 資源使用 `projectcalico.org/v3`，套用緊接 CRD 建立時 admission 出現 `paramKind` discovery 錯誤 | 確認 Calico v3.33 CRD 已 `Established`、目標 Kind 已在 API discovery，再重試原本那一個受影響的 admission 動作。只對已識別的暫時 discovery race 做短延遲、有限次數重試；其他 schema/admission 錯誤立即失敗。 | 重試上限建議 3 次，退避例如 2 秒；持續失敗即停止查 webhook/CRD 狀態。不可無限重試或包住整批安裝。 |
| EndpointSlice `endpointslice.kubernetes.io/managed-by` 標籤值驗證失敗 | 檢查的是 label **value**。Kubernetes label key 可以有 `/` 前綴分隔，value 不可包含 `/`；將管理者值改成符合 label-value 語法的字串。 | 不要為修 value 而移除 key 的 domain prefix；也不要把 annotation 語法套到 label value。 |
| Indexed Job 的 `successPolicy` 驗證失敗或成功條件不符預期 | 比對 `.status.succeeded`、`.status.completedIndexes`、`.spec.completions`、`completionMode` 與每條 rule。若同一條 rule 設 `succeededIndexes: "0"`，其 cardinality 是 1，`succeededCount: 4` 會因 count 超過該 rule indexes 數而無效；只要求任意 4 個成功時省略 `succeededIndexes`。多條 rule 是 OR，無法用 `successPolicy` 表達「index 0 必須成功且總共 4 個成功」的 AND 條件。 | Pod 成功數不是 completed index 集合；按同一條 rule 驗證 `succeededCount` 與 `succeededIndexes` cardinality。先確認目標 Kubernetes 版 API/控制器文件，不要把多條 OR 規則當 AND。 |
| YAML parse 成功但套用/程式碼錯誤，或 Pod 缺欄位 | 先檢查 code fence 是否把範例文字混進 YAML、每個 container 是否有必要 `name`，及 `securityContext` 位於 Pod-level `spec.template.spec.securityContext` 或 container-level `spec.template.spec.containers[].securityContext` 的正確層級。再跑目標 API strict server dry-run。 | YAML 語法有效不代表 Kubernetes schema 有效；client-side parse 不代替目標伺服器驗證。 |
| cert-manager 或 issuer 範例因 email/網域 placeholder 失敗 | 將 placeholder 標成範例輸入，只在隔離 QA render 時以明確測試值取代；檢查最後產物是否仍含 `<...>`、`user@example.com` 等未設定值。 | 測試值、私人網域及 QA secret 不進 source、public fixture 或 publication staging。不要把 QA render 當成可直接上線的 manifest。 |
| informer watch 無事件、卡在啟動、結束後 goroutine 留存或錯誤被吞 | 依序檢查 client 建立錯誤、informer factory 啟動、cache sync、handler sync、watch/RBAC 錯誤、事件 handler error path、signal/context cancellation、factory shutdown。對照 [`examples/client/informer/informer.go`](../examples/client/informer/informer.go)：先等待 cache 與 handler sync，透過 context 結束，defer factory shutdown，向上傳遞初始化錯誤。 | 不要把 `WaitForCacheSync` 或 watch timeout 當作可忽略狀態；事件 handler 的錯誤處理要與工作負載語意一致。 |
| Node Problem Detector 參數 `--logtostderr` parser 可讀但 `--help` 清單找不到 | 查精確 release 的 flags 定義和解析器行為。某些隱藏/相容參數可能不列在 help 清單；以 parser/source 和實際目標版本驗證，不只用 help 輸出判定不存在。 | source 接受 flag 不等於目標部署安全或 Kubernetes 相容性已驗證。 |
| Python 工具說缺少 `jsonschema`，但已安裝套件 | 比較 `python`、`python3`、`which python*` 與 `python -m pip show jsonschema` 的 interpreter 路徑；用同一 interpreter 執行程式和 pip。優先在 repo 外的臨時 venv 安裝所需測試相依。 | 不要直接改系統 Python 或全域套件；僅 `pip show` 在另一個 interpreter 有結果不能證明執行環境已安裝。 |
| Git 上大小寫不同的 PNG 在 macOS 等大小寫不敏感檔案系統似乎消失 | 用 `git ls-files` / `git ls-files --stage` 比對精確路徑與 staged index；勿用 `find`、`test -f` 或 case-folded 名稱推斷 Git tree。 | `git add` 或檔案系統複製可能遺漏只差大小寫的 tracked 檔；若未改動的資產缺失，應從原始 Git blob 恢復，不假設磁碟副本保留兩份。 |
| `gitbook install` 失敗 `Missing required argument #1` | 先記錄 Node/npm/GitBook CLI 的精確版本。隔離環境中 GitBook 3.2.3 搭配 npm 3.9.2 的 plugin installer 會報 `Missing required argument #1`。這是舊工具鏈錯誤，不是書稿 build 成功。 | 不要把升級根專案相依或重寫 GitBook 架構混入單一內容修正；先停止舊 installer 路徑並回報受阻。 |
| 跳過 `gitbook install` 後 `make build` 仍失敗或解析到 plugin prerelease | 已知 QA-only workaround 使用 npm 6 安裝 plugins 後，`make build` 仍因 `gitbook-plugin-github@3.0.0` 要求 GitBook `>=4.0.0-alpha.0` 而失敗；npm `search-plus` 的 `latest` dist-tag 曾解析為 `1.0.4-alpha-3`。檢查實際安裝 tree、peer/dependency range 和 dist-tags，不從 `latest` 字樣推定 stable。 | 這是目前已觀察到的舊相依相容性 blocker。它沒有證明來源章節錯誤，也沒有證明 production GitBook render 通過；不要再把 QA-only plugin install workaround 當正式建置修復。除非另有明確任務，不做根專案框架遷移。 |

## 驗收

重現步驟、目標版本/context、錯誤與修正前後結果可重做；修改只處理已證明根因。每項檢查標為通過、失敗、受阻或未執行。特別是 GitBook 舊工具鏈 blocker 必須保留錯誤和相依版本，不能宣稱最新 production build/render 已成功。

## 限制

不對正式叢集套用 debug 修改，不關閉驗證或弱化 source 安全設定來讓測試變綠。暫時性重試必須限於已識別錯誤、單一動作和明確上限。未能重現時標記未知，不猜測成功原因。
