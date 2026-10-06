# Kubernetes v1.37 元件相容性追蹤

[元件追蹤清單](component-watchlist.json)記錄 Kubernetes v1.37.1 的特定支援缺口與[元件版本清單](component-versions.md)中的版本基準。快照與人工審查支援狀態的日期均為 2026-10-05。清單會區分元件的獨立版本基準與 kubeadm 預設固定版本。例如，Kubernetes v1.37.1 固定使用 etcd 3.7.0 與 CoreDNS 1.14.6；兩者的獨立版本基準則分別是 etcd 3.7.2 與 CoreDNS 1.14.7。k0s 與 RKE2 列出各自的發行版版本；內含的 Kubernetes 版本及元件不是 kubeadm 固定值。

pause 映像檔固定使用 3.10.2。來源清單沒有記錄它的獨立穩定版基準，因此檢查器不會查詢該映像檔，固定版本仍由人工依來源資料審查。

上游發布較新的版本，不代表該版本相容於 Kubernetes v1.37，也不會改變版本基準或固定版本。檢查器會讀取 GitHub 公開 Releases API，略過草稿版及預先發布版，再將穩定版的語意化版本號與清單中的基準比較。k0s（`+k0s.N`）與 RKE2（`+rke2rN`）的穩定建置後綴是發行版的數值重建修訂號，不是預發布標記；檢查器只在各自發行版內比較修訂編號，不會改變其他專案的 SemVer build metadata 排序。未知的發行版後綴會使檢查失敗。檢查器不讀取相容性頁面、不修改來源檔案、不選擇版本、不認證支援狀態，也不建立 issue。請人工查閱官方支援連結並更新相容性狀態。

## 執行版本檢查

在儲存庫根目錄使用 Python 3 標準函式庫即可執行。以下指令可跨平台使用，會將 JSON 報告寫入 `/tmp`，並輸出簡短摘要：

```sh
python3 scripts/check-component-updates.py --output /tmp/kubernetes-component-updates.json
```

JSON 報告會列出 UTC 檢查時間、各元件的基準版本與最新穩定版，以及是否有較新版本需要人工審查。人工審查的相容性欄位會列在 `baseline_support`，並包含 `reviewed_version`。這些欄位只適用於清單記錄的基準版本，不適用於較新版本。若網路請求失敗或 API 回應格式錯誤，檢查器會產生錯誤報告並以非零狀態結束。只要有一個受追蹤的儲存庫無法檢查，檢查器就不會回報「沒有更新」。

檢查器會為每個受追蹤儲存庫分頁讀取 GitHub 公開 Releases API，並比較最高的穩定語意版本；不會只採用第一個穩定發布項目，也不會只依 `/releases/latest` 的發布順序判定。`tag_prefix` 與 `tag_exclude_prefixes` 可界定含多種產品的儲存庫範圍（例如 containerd 的 `api/` 發行、autoscaler charts，以及 kube-state-metrics charts）；精確標籤排除僅限追蹤清單中有來源和日期記錄的 CoreDNS、Cilium 與 Grafana 舊標籤。仍有符合所選產品範圍的未知穩定標籤時，檢查器會拒絕放行。一般儲存庫最多查詢 10 頁（1,000 筆發行）；RKE2 最多查詢 13 頁（1,300 筆），目前資料佔 12 頁。未設定 `GITHUB_TOKEN` 時，單次執行最多送出 55 次公開 API 請求後即停止。目前追蹤清單包含 29 個儲存庫，完整掃描所需請求超過 55 次；未經驗證的掃描會因超過本地請求上限而失敗，不會回報乾淨的部分結果。若要完成整份清單的掃描，須提供 `GITHUB_TOKEN`。檢查器只會在查詢公開 Releases API 的 GET 請求中透過 Authorization 標頭傳送該 token，並將本地總請求上限提高至 500 次；500 次是檢查器的上限，不是 GitHub 保證提供的 API 配額。各儲存庫的分頁上限仍適用。任何不完整掃描都會回報錯誤。

選用的 `--fixture FILE` 參數可讀取固定的離線發布資料，供測試使用。檔案採 JSON 格式，包含 `schema_version: 1` 與 `releases` 物件；`releases` 以每個受追蹤的 `owner/repository` 為鍵，值則使用 GitHub Releases API 清單格式。fixture 必須列出追蹤清單中的每個儲存庫。一般檢查不需要 fixture。

## 審查更新

對每一筆 `review_required: true` 的報告項目：

1. 開啟追蹤清單中該元件的官方 `support_url`，查閱 Kubernetes 1.37 對應版本的支援矩陣或發布說明。
2. 查核上游發布版本，以及另行記錄的 kubeadm／來源固定版本。kubeadm 預設值不代表一般性的相容保證。
3. 修改人工維護的版本清單或支援狀態前，先在隔離叢集中測試預定使用的版本組合。

檢查器不會代為修改這些欄位。追蹤清單中的 `support_status`、`supported_kubernetes_range`、`support_notes` 及 `support_reviewed_on` 都是明確的人工紀錄。`null` 表示清單尚未記錄支援範圍，不表示所有 Kubernetes 版本都受支援。

## 每週報告

`Component release watch` 工作流程每週執行一次，也可手動觸發。工作流程僅授予 `contents: read` 的唯讀儲存庫權限，並只在檢查器步驟中透過 `GITHUB_TOKEN` 環境變數提供其內建 token，供查詢公開 Releases API 的 GET 請求使用。檢查器不會顯示或儲存 token。工作流程會將 JSON 報告上傳為工作流程成品；檢查失敗時，工作流程仍會失敗，即使同時上傳錯誤報告供診斷。工作流程不會發布網站內容或編輯 issue。
