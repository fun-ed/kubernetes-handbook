# 目前內容更新檢查

本次檢查以 Kubernetes **v1.37.1** 為基準，以 v1.36、v1.37 為比較範圍，資料截點為 **2026-10-05**。起始清單列出 176 篇正式 Markdown 文件；另核對新發現的憑證管理指南、程式與資訊清單檔案、映像檔參照、繁體中文對應頁及根目錄導覽。逐檔路徑、檢查結果、封存對照與版本證據見[機器可讀檢查清單](current-content-review.json)。簡體中文版的檢查記錄見[現行內容檢查記錄](https://github.com/fun-ed/kubernetes-handbook/blob/main/setup/current-content-review.md)。

## 檢查範圍

各領域負責人分別檢查基礎概念與元件、部署與擴充、工作負載、網路與疑難排解、範例及元件清單。根目錄另檢查 `README.md`、`SUMMARY.md`、`CHANGELOG.md`、`plugins/index.md` 與維護 SOP。`coverage.json` 逐項列出目前 Markdown 對應頁、排除理由、封存內容與資源檔案；舊原文由新指南取代時仍列為目前內容，並另外記錄封存副本。

目前的嚴格 Markdown 檢查共掃描 359 個檔案：178 對現行中文文章（356 個檔案），以及根目錄 3 份治理文件（`AGENTS.md`、`CODE_OF_CONDUCT.md`、`CONTRIBUTING.md`）。這 3 份文件不屬於繁體中文翻譯範圍；英文 `en/` 與封存內容也不列入現行文章配對清單。

`archive/index.md` 保留原有 100 筆整頁封存記錄及 Azure GPU 歷史片段記錄，並補上新封存的非 Markdown 範例、目前頁面改寫對照與拆出的歷史片段。根目錄 `.bookignore` 會排除封存目錄，因此封存內容不屬於目前書籍導覽或目前資訊清單驗證範圍。

## 已修正的目前內容

- 移除或更正過期 API、舊版控制器設定、過時執行階段參數、失效安裝步驟，以及權限或憑證處理不當的範例。歷史原文仍供查閱，不作為目前部署指引。
- 區分 Kubernetes 資源行為與特定發行版、控制器或雲端服務功能。找不到 v1.37 支援聲明的元件明確標示為未知；不會只憑較新的版本號推定相容。
- 更新負載平衡、Service、EndpointSlice、HPA 指標、CSI、節點排錯與平台限制說明。已移除未限制公開範圍的通用 RDP `LoadBalancer` 範例，並將舊版 Windows 與網路實驗資訊清單移出目前路徑。
- 修正叢集排錯頁的 DNS 指令範例缺少結束程式碼圍欄，導致後續 Dashboard 與 HPA 章節落入程式碼區塊的結構問題。釐清指標 API 範圍：Kubernetes 的 `metrics.k8s.io/v1` 已達穩定版，但以本書基準為準，Metrics Server v0.9.0 僅提供 `metrics.k8s.io/v1beta1`，Kubernetes v1.37.1 的 HPA 也使用該 API；`kubectl top` 可先查詢 v1，再回退至 v1beta1。另補充 APIService、API 聚合及指標採集流程的排查界線。
- 全面檢查目前文章中的映像檔參照：共有 252 處 `image:`／`--image`，包含 29 個不同值。已分開記錄已核對標籤存在性的項目、教學佔位符、使用者設定變數、仍須核對的外部參照及可變標籤。已發現並修正過期 NGINX 與 Go 建置映像檔；CUDA 教學範例仍保留其 CUDA 版本需求，上游標籤查詢受限時沒有猜測新版本。標籤存在不代表元件受 Kubernetes v1.37 支援。
- 逐項靜態盤點 `examples/` 與 `manifests/` 下 65 個非 Markdown 檔案，擷取出 108 筆 API 資源描述。這不等於 API Server、CRD、控制器或工作負載的實際執行驗證。

## 版本證據與限制

Kubernetes API 與相依版本以 [v1.37.1 上游標籤](https://github.com/kubernetes/kubernetes/tree/v1.37.1)、[版本淘汰指南](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)及[相依清單](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml)核對。第三方元件版本、支援聲明與相容性證據分別記錄於[元件版本清單](component-versions.md)及機器可讀檢查清單。

本報告不宣稱所有元件、雲端平台、CNI／CSI 驅動程式、Windows 節點或正式環境都支援 v1.37。沒有廠商相容性矩陣或實際環境時，執行狀態仍屬未知。映像檔標籤核對也不等於固定 digest、架構驗證或端到端部署認證。

## 驗證狀態

內容負責人沒有自行執行測試、建置、lint、格式化、安裝、叢集或雲端指令。以下為主整合者實際執行的檢查結果；逐項範圍與結果記錄於機器可讀檢查清單。

* Python 內容測試 53 項、npm 測試 12 項及 Go informer 迴歸測試 3 項均通過；另有 5 個 CRD 驗證程式庫迴歸案例通過（接受 1 個有效物件，拒絕 4 個無效物件）。
* 獨立清單檢查涵蓋 54 個 YAML 檔案、108 個資源物件；91 個內建資源通過 schema 驗證，17 個自訂資源未在本機驗證。
* 目前文章內嵌檢查掃描 359 篇 Markdown 和 384 個 YAML 圍欄，共處理 326 個內建資源物件：316 個通過嚴格 JSON Schema 驗證，另有 10 個 CRD 通過 Kubernetes v1.37.1 官方 Go 驗證程式庫檢查。此外，26 個自訂資源及 8 個原生設定物件未經驗證；42 個純資料文件和 0 個範本不納入物件驗證。驗證過程未出現錯誤。Go 驗證程式庫檢查不等同 API Server dry-run。
* 唯讀檢查 26 個元件的上游更新狀態，共送出 85 次請求，沒有請求錯誤；截至資料截點，未發現比清單基準更新的穩定版。這不代表任何元件已確認支援 Kubernetes v1.37。

最終建置、渲染及輸出連結檢查結果見機器可讀檢查清單；本次沒有執行 GitHub Actions、API Server、叢集或雲端部署驗證。以上檢查通過不構成正式環境相容性聲明。

歷史升級記錄仍見[變更歷史](../CHANGELOG.md)及[v1.37.1 相容性指南](kubernetes-v1.37.md)。歷史記錄保留原日期和當時測試範圍，不代表本次新增檢查結果。
