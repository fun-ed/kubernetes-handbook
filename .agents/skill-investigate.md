---
name: skill-investigate
description: 調查 Kubernetes 版本升級、元件發布與相容性、API 移除、歷史清單或變更責任範圍時使用。先取得固定截點與正式來源證據，再區分上游最新、Kubernetes 固定值、支援聲明及實測結果。
---

# 升級調查 SOP

## 觸發與前提

當工作要新增或更新 Kubernetes／外掛元件版本、排查舊 API、判定歷史範例是否仍可用，或拆分升級調查工作時使用。從倉庫根目錄開始，先讀取 [AGENTS.md](../AGENTS.md)、[Kubernetes v1.37 指南](../setup/kubernetes-v1.37.md)、[元件版本清單](../setup/component-versions.md)及[清單狀態說明](../manifests/README.md)。本倉庫的基準為 Kubernetes v1.37.1，資料截點為 2026-10-05；除非任務明確更改，調查結果不得把截點後資料混入基線。

## 步驟

1. **固定問題邊界。** 記下目標 Kubernetes patch/minor、元件、作業系統與 CPU 架構、用途、目前部署版、截點及預期交付檔。區分本地原始碼、手冊範例、測試叢集和正式環境，不把一種環境的結果套用到另一種。檔案盤點以 `git ls-files` 的精確大小寫路徑為準；大小寫不敏感的檔案系統可能摺疊只差大小寫的 tracked paths，不以 `find` 或檔案存在狀態代替 Git tree。
2. **依正式證據確認 release。** 優先讀專案官方 release 頁/API、官方 tag、正式 artifact 登錄庫及該 tag 的文件。逐一記錄精確 tag、release/published 日期與時區、draft/prerelease 狀態、來源 URL、artifact 名稱及 digest。發佈列表日期與 GitHub `published_at` 不同時保留兩個日期及來源，不自行挑一個覆蓋另一個。

   下列命令列出 GitHub 正式 Release API 資料；`awk` 只按 UTC 時間字串篩除截點之後的紀錄，仍須檢查 tag 名稱和 upstream release 語意，因為不同專案的 prerelease 標記方式不完全相同。

   ```bash
   # 前提：gh、awk；REPO 使用 org/project 格式。
   REPO='kubernetes/kubernetes'
   gh api --paginate "repos/$REPO/releases?per_page=100" \
     --jq '.[] | select(.draft == false and .prerelease == false) | [.tag_name, .published_at, .html_url] | @tsv' \
     | awk -F '\t' '$2 <= "2026-10-05T23:59:59Z"'
   ```

   這份列表不包含沒有 GitHub Release 物件的 tag，也不能單靠 `prerelease:false` 判穩定。檢查 tag 字串是否含 alpha、beta、rc 或專案定義的預發布標記；需要時查該專案的 tags、官方版本政策與 release notes。npm 的 `latest` dist-tag 也可能指向預發布版，先查 `npm view <package> dist-tags --json`，再固定並記錄實際版本，不以 dist-tag 名稱當穩定證據。
3. **分開記錄版本與相容性。** 對每個元件分欄記錄「截點前最新正式穩定版」、「Kubernetes/kubeadm 原始碼或預設固定值」、「官方明示支援/測試範圍」、「本次實際驗證範圍」。最低版本要求、同 minor 命名、tag 存在、能下載或能安裝，都不等於目標 Kubernetes 版本已測試或受支援。對未找到證據的格子寫「未找到官方 v1.37 支援聲明」或「本次未測試」，不得推論相容。
4. **讀發佈時文件，不用 live 文件代替。** 對相容性及安裝行為優先引用精確 release tag 下的 README、文件和 release notes；live/latest 文件只作為「現行文件」另列。若兩者內容有差異，記錄文件版本、差異和採用理由。記錄 image/chart/controller/CRD 各自版本，不能拿 Gateway API CRD 版本代替 controller 支援聲明。
5. **核對 artifact 和架構。** 對容器映像讀 OCI index/manifest digest，確認目標節點架構如 `linux/amd64`、`linux/arm64`；對二進位套件記錄平台與 checksum。需要查 registry 時使用精確 tag，例如：

   ```bash
   # 前提：docker buildx；IMAGE 必須是已確認的完整映像名稱與 tag。
   docker buildx imagetools inspect "$IMAGE"
   ```

   可下載不等於目標架構可執行；amd64 實測也不證明 arm64。沒有查到架構時標成未知。
6. **核對 Kubernetes 內建版本。** 對 kubeadm 安裝路徑直接查目標 Kubernetes tag 的 dependencies/defaults，並以該版本執行 `kubeadm config images list --kubernetes-version v1.37.1` 核對實際映像。v1.37.1 kubeadm 的 etcd 3.7.0、CoreDNS 1.14.6、pause 3.10.2 是其固定值，不是各 upstream 的最新版本，也不是第三方相容保證。比較上游最新版時保留兩欄，不用較新的 release 自動覆蓋 kubeadm pin。
7. **審核退役項目和 API。** 對舊元件查官方 archived/EOL/retired 聲明，不以「多年沒更新」單獨判定退役。對 API 先檢索實際 `apiVersion`，再依目標版官方 deprecation/removal 文件核對；記錄資源、檔案、是否有 `HISTORICAL` 標記、替代方式和是否仍由目前安裝路徑引用。舊清單保留作教學時不得併入當前安裝命令。

   ```bash
   # 前提：rg；只列路徑及 API 欄位，逐筆判斷歷史標記與實際用途。
   rg -n --glob '*.yaml' --glob '*.yml' --glob '*.json' '^[[:space:]]*apiVersion:' examples manifests deploy
   rg -n 'HISTORICAL:' examples manifests deploy
   ```

   叢集側可在明確指定的測試 context 查 API discovery 與棄用指標；沒有指標資料不能解讀成沒有舊 API 使用。

   ```bash
   # 前提：已確認是測試叢集，KUBE_CONTEXT 指向該 context。
   : "${KUBE_CONTEXT:?設定精確的測試 context}"
   kubectl --context "$KUBE_CONTEXT" api-resources
   kubectl --context "$KUBE_CONTEXT" get --raw /metrics \
     | grep '^apiserver_requested_deprecated_apis'
   ```
8. **拆分工作並約束並行。** 建立明確清單：檔案/元件、單一 owner、依賴、驗證方式、證據來源及交付時間。並行工作必須擁有互不重疊的檔案範圍；共享清單、跨檔 API/版本決策和最後整合指定一位 owner。交接時說明不能推論的相容範圍及未解問題，不以同一目錄作為足夠的責任界線。

## 驗收

調查記錄對每一個目標版本都有可點開的正式來源、截點前的穩定性證據、架構/artifact 資訊或明確未知狀態，並把 upstream 最新、Kubernetes 固定值、支援聲明及實測結論分開。API/歷史清單已標出，不會被當成目前安裝輸入；各工作有單一 owner 與不衝突的檔案範圍。

## 限制

此 SOP 不宣告未查證的支援矩陣、不替生產環境執行升級，也不把一次 smoke test 擴大成產品認證。需要更新本倉庫版本基線時，只改相應章節並保留日期、來源與證據差異；不要在本文件複製整份[版本矩陣](../setup/component-versions.md)。
