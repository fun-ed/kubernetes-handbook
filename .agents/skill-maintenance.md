---
name: skill-maintenance
description: 維護或升級 Kubernetes v1.37 手冊、元件與 manifests，執行版本/安全檢查、測試驗證、回滾規劃或已核准的 GitHub clean-snapshot publication 時使用。依序完成盤點、備份、隔離驗證、回滾與發佈檢查。
---

# 維護與升級 SOP

## 觸發與前提

當更新本手冊的 Kubernetes/元件基線、範例 manifest、Go/Python 範例、GitBook 文件或執行已核准的升級/公開發布時使用。先讀 [AGENTS.md](../AGENTS.md)、[Kubernetes v1.37 指南](../setup/kubernetes-v1.37.md)、[元件版本清單](../setup/component-versions.md)及[manifest 狀態說明](../manifests/README.md)。一般維護只影響工作樹；連接叢集、備份/還原、建立遠端 repo、改 remote 或 push 前確認任務已授權。所有命令要有明確輸入，不以 `kubectl` default context 或 production context 當測試目標。

## 流程

### 1. 盤點與凍結目標

1. 記錄來源分支/工作樹狀態、修改檔案、目標 Kubernetes patch、截點、部署工具、架構、CRI/CNI/CSI、准入/監控/網路元件及外部資料相依。指定每個檔案唯一 owner；共享版本、schema 和最後驗收指定整合 owner。
2. 以 [元件版本清單](../setup/component-versions.md)作版本來源，不複製一份容易過期的完整矩陣。分開記錄上游最新正式版、Kubernetes/kubeadm pin、官方支援矩陣及本次實測。artifact 必須固定 tag/digest 與目標架構；檢查 CRI v1、cgroup driver、OS/security profile。不得因版本號較新或同 minor 推定相容。
3. 先盤點舊 API、已刪除 feature gate/參數和歷史資源。保留 `HISTORICAL` 標記；清單目錄同時含 current 與歷史檔案時逐檔指定，絕不遞迴套用整個目錄。查看 [manifest status](../manifests/README.md) 的歷史資源表。
4. 保留最低權限、唯讀 root filesystem、明確 seccomp/capabilities、非 root、資源 requests/limits、憑證輪替等適用的安全設定。只在確認需求及威脅模型後改安全 profile；不能為通過 QA 永久放寬 TLS、權限或 admission。

### 2. 備份與回滾先行

正式升級前備份 etcd、叢集與 kubeadm 設定、憑證/外部資料庫/持久卷及工作負載資料，並記錄一致性時間與還原負責人。在隔離環境實際驗證快照還原和應用資料恢復，再排維護窗口、節點順序、健康門檻、流量切換及停止條件。依部署工具支援的版本逐個 Kubernetes minor 前進，每步按工具及元件官方 upgrade guide 操作。

Kubernetes 不把升級後 control plane 直接降版當通用回滾。預先寫清楚採用支援的恢復流程、何時停手、如何處置資料寫入及由誰核准還原。快照未恢復驗證或應用資料無復原計畫時，不升級正式環境。

### 3. 在隔離測試叢集驗證

使用組織明確指定的 disposable/test context 和 kubeconfig 路徑。不能只憑 `kind-*` 名稱判斷環境安全，核對 context 指向的 API server、節點版本與資源歸屬。每個操作都顯式帶 `--kubeconfig`、`--context`，絕不依賴目前 default context。

```bash
# 模板。前提：兩個變數都由操作者明確設定為 disposable/test 環境。
: "${KUBECONFIG:?設定測試 kubeconfig 的明確路徑}"
: "${KUBE_CONTEXT:?設定 disposable/test context 名稱}"
kubectl --kubeconfig "$KUBECONFIG" config get-contexts "$KUBE_CONTEXT"
kubectl --kubeconfig "$KUBECONFIG" --context "$KUBE_CONTEXT" version
kubectl --kubeconfig "$KUBECONFIG" --context "$KUBE_CONTEXT" get nodes -o wide
kubectl --kubeconfig "$KUBECONFIG" --context "$KUBE_CONTEXT" get --raw='/readyz?verbose'
```

先驗證 CRD 定義本身，再等待目標 CRD `Established` 並確認 `kubectl api-resources` discovery；接著驗證對應自訂資源。對**所有已審查且屬於目前安裝路徑的檔案**逐檔執行 strict server dry-run，包含 Kubernetes built-in API 和已安裝的 vendor CRD schema。Server dry-run 需要 API、schema 及 admission webhook 已就緒；缺 CRD 時先記錄前置條件未滿足，不改成略過驗證。

```bash
# 模板。把陣列內容換成逐檔審查過的 active manifests；不要放目錄、歷史檔或未設定範本。
ACTIVE_MANIFESTS=(
  'manifests/example/current.yaml'
)
: "${KUBECONFIG:?設定測試 kubeconfig 的明確路徑}"
: "${KUBE_CONTEXT:?設定 disposable/test context 名稱}"
for file in "${ACTIVE_MANIFESTS[@]}"; do
  test -f "$file" || { printf 'missing manifest: %s\n' "$file" >&2; exit 1; }
  kubectl --kubeconfig "$KUBECONFIG" --context "$KUBE_CONTEXT" \
    apply --dry-run=server --validate=strict -f "$file" || exit 1
done
```

接著驗證 node readiness、CoreDNS/DNS 查詢、Pod 網路、Service/Gateway HTTP 與 HTTPS、憑證、持久卷、准入、metrics/APIService、告警和實際工作負載。Gateway 測試要核對 listener 80/443、Traefik Service `port`/`targetPort`、Pod/container port 及 Traefik entryPoint 的實際映射；目前範例的 Gateway 與 Service 使用 80/443，不要沿用舊的 8000/8443 假設。CRD/server dry-run 不驗證 controller 行為、資料面或雲資源。

如 QA 需要自簽或不驗證 kubelet TLS 的測試設定，只在 disposable QA render/測試輸入使用，標記為 QA-only 並在測試後清除。不要把 `--kubelet-insecure-tls` 或關閉憑證驗證寫入 production source/預設 manifest。

### 4. 驗證內容、程式與文件

- 逐一檢查修改的 YAML、必要 container name、`securityContext` 層級、code fence、連結與 placeholder。對每個 manifest 跑前述 strict dry-run；不能用遞迴套用 `manifests/`。
- 檢查 diff、空白和修改檔案清單。此倉庫沒有統一 Markdown/YAML lint 設定；手動核對 Markdown fences、內部連結、anchor 和圖片相對路徑。簡單 fence 配對可用下列命令初查，仍需人工檢查 nested fence 與 tilde fence：

  ```bash
  git diff --check
  git diff -- '*.md'
  git diff --cached -- '*.md'
  ```

- Go 變更在對應 `go.mod` 所屬 module 執行 `go test ./...` 和 `go vet ./...`。如輸出 `? ... [no test files]`，照實註明沒有 unit test 檔，不能把套件編譯等同功能測試。
- Python 驗證先用同一個 `python -m pip` 與 `python` 確認套件安裝位置，必要時在 repo 外臨時 venv 裝依賴；不要以其他 interpreter 的 `pip` 結果判斷環境。
- GitBook 命令按 [AGENTS.md](../AGENTS.md)、`Makefile`、`package.json` 與 `book.json` 實際定義執行。`npm test` 是明確失敗的 placeholder，不是測試。此倉庫目前已觀察到外部舊建置阻塞：首次 `make build` 缺少 `gitbook`；隔離 Node 10 / GitBook 3.2.3 / npm 3.9.2 的 plugin installer 回報 `Missing required argument #1`；QA-only 以 npm 6 繞過 installer 後，`make build` 仍因 `gitbook-plugin-github@3.0.0` 要求 GitBook `>=4.0.0-alpha.0` 而失敗，且 `search-plus` 的 `latest` dist-tag 曾選到 `1.0.4-alpha-3`。保留完整版本與錯誤作為**來源相依相容性 blocker**，不要聲稱 production render/build 通過，也不要為內容任務擴大成根框架遷移。若之後環境或依賴變更，重新實測並另行記錄結果。

每次報告分項列出實際執行命令、結果、未執行項及阻塞原因。lint/build 沒有跑不能寫成 pass；server dry-run pass 不代表 smoke test pass。

### 5. 回滾與資源清理

升級前定義並演練回滾：控制平面與節點使用各自受支援的復原程序；etcd 快照要實際還原驗證；外部資料庫/PV/應用資料按一致性策略恢復。升級期間逐節點觀察 readiness、排程、網路/DNS、儲存和業務 SLI，觸及預先定義的停止門檻就暫停後續節點。回滾前評估新版本寫入的資料和 schema 是否向後相容。

清理只限本次建立且能證明由本次工作擁有的測試叢集、映像和暫存金鑰/檔案。刪除前逐項核對名稱、建立時間、owner label 和目前引用；不執行 `kubectl delete` 對未知資源、不執行 `docker system prune`/`image prune`，也不清除使用者或共用環境資料。

### 6. 已核准的 GitHub clean-snapshot publication

本專案已明確選擇**新建 public `fun-ed/kubernetes-handbook`，以乾淨 snapshot 建立新 `main`，不公開原始 Git 歷史**。保留原 `master`/來源 remote 與 commit 歷史在本機。此策略為核准的特定決定；未來若要改成保留/重寫歷史，先取得明確核准，不自行更換策略。

1. 檢查工作樹、目前分支與 remotes，確認原始來源 remote 可辨識且不刪除；把 `.git/config` 備份到 repo 外私有目錄。該檔可能含內部 remote/config，設目錄 `700`、檔案 `600`，不要輸出或發布備份。

   ```bash
   # 前提：從倉庫根目錄執行；TMPDIR 必須是本機私有暫存位置。
   set -eu
   test -f .git/config
   BACKUP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/k8s-handbook-git-config.XXXXXX")"
   chmod 700 "$BACKUP_DIR"
   cp .git/config "$BACKUP_DIR/config"
   chmod 600 "$BACKUP_DIR/config"
   printf 'Private config backup: %s/config\n' "$BACKUP_DIR"
   git status --short
   git branch --show-current
   git remote -v
   ```

2. 確認 GitHub CLI 已登入且使用者為 `fun-ed`。用 authenticated API 建立 public、空 repo，不用瀏覽器初始化 README，也不在 remote 建第二個 root commit。已存在或 owner 不符時停止並人工確認，不刪除/覆寫 repo。

   ```bash
   # 前提：gh 已安裝並以有權限的 fun-ed 帳號登入。
   gh auth status
   test "$(gh api user --jq .login)" = 'fun-ed'
   gh api -X POST user/repos \
     -F name='kubernetes-handbook' \
     -F private=false \
     -F auto_init=false
   ```

3. 準備明確 publication allowlist，只包含已審查的手冊、來源、授權與必要設定。新 `main` 必須沒有舊 commit ancestry；將原 branch/remote 留在本機作來源參照，將新 HTTPS remote 命名為 `origin`，原來源 remote 改用清楚的名稱如 `source`。先查實際 remote 名稱，避免覆蓋既有 remote。
   在變更 remote 前先把原始來源 remote 名稱和 URL 記入本機備忘，並確認 `source` 尚未存在。下列命令只適用於原始 remote 目前叫 `origin` 的情況；名稱不同時按實際名稱調整。完成後檢查新 `origin` 必須是 HTTPS。

   ```bash
   # 前提：已建立空的 fun-ed/kubernetes-handbook；原 origin 是來源 remote；source 名稱尚未使用。
   git remote -v
   git remote rename origin source
   git remote add origin https://github.com/fun-ed/kubernetes-handbook.git
   git remote -v
   ```
4. 建立 orphan `main` 並逐條加入 allowlist，不使用 `git add -A`、`git add .` 或 force-add 全目錄。exclude `.git/`、`.serena/`、QA secret/credential、kubeconfig、私人測試資料、build output；不把 exclusion 寫成 blanket scanner ignore。`git diff --cached --name-status` 必須逐項核准後才 commit。以下為**人工審查後才可執行的模板**，佔位路徑要替換成實際 allowlist：

   ```bash
   # 前提：origin 不會覆蓋原始 remote；main 在本地不存在；目前工作樹檔案已確認可保留。
   # `checkout --orphan` 保留目前工作樹與 index；先記下 allowlist 雜湊。
   shasum -a 256 README.md SUMMARY.md AGENTS.md LICENSE .agents/skill-investigate.md .agents/skill-debug.md .agents/skill-maintenance.md 'path/to/other-reviewed-file'
   git checkout --orphan main
   # 只清空 index，不加 -u，不更新或刪除工作樹檔案。
   git read-tree --empty
   git status --short
   # 核對 allowlist 雜湊與 checkout 前完全相同，再加入明確路徑。
   shasum -a 256 README.md SUMMARY.md AGENTS.md LICENSE .agents/skill-investigate.md .agents/skill-debug.md .agents/skill-maintenance.md 'path/to/other-reviewed-file'
   git add -- README.md SUMMARY.md AGENTS.md LICENSE .agents/skill-investigate.md .agents/skill-debug.md .agents/skill-maintenance.md 'path/to/other-reviewed-file'
   git ls-tree -r --name-only master
   git ls-files
   git diff --cached --name-status
   git diff --cached --check
   ```
   `checkout --orphan` 留下原始 branch（包括本機 `master`）與工作樹。dirty tree 的舊 index 可能和工作樹內容不同，`git rm --cached` 會拒絕；用不帶 `-u` 的 `git read-tree --empty` 清空 index，然後比對 allowlist 前後雜湊。不要用會改動 working tree 的清理命令，也不要刪除原始 source branch/remote。

   大小寫不敏感的檔案系統可能使 `git add` 摺疊只差大小寫的 tracked paths。將 `git ls-tree -r --name-only master` 與 `git ls-files` 的精確路徑集合對照人工 allowlist；不可由 `find`、檔案存在或磁碟複製推定兩個變體都保留。未變動的資產若缺漏，從原始 Git blob 保留，並驗證 staged tree 路徑集合。

   `git add` 中的目錄只可用於已人工確認不含 `.serena`、QA secret、歷史/私人資料或生成輸出的來源子目錄；更安全做法是逐檔列路徑。保留原始作者/來源歸屬、根目錄 CC BY-NC-SA 4.0 授權與 Apache 授權子樹的 LICENSE/NOTICE；不要把新 repo 版權改成自己的，也不要把原 upstream 歷史 SHA 說成新 repo commit。
5. 執行 secret scanner 檢查 staging/worktree，分類每個 finding 為真實秘密、已遮蔽的測試 fixture 或可證明的 false positive；真實 credential 一律移除/輪替。必要時只對已審查 fixture 設精準、附理由的 scanner 設定。不得加入 blanket ignore、不得以 `.serena` 或 QA 路徑為由遮掉整個掃描範圍。檢查所有自有 repo 連結並將導覽連結改為 `https://github.com/fun-ed/kubernetes-handbook/blob/main/...`；來源歸屬網址依授權保留，不能將它誤判為自有導覽。

   ```bash
   # 前提：rg；只檢查 repo 自己的網址，命中後人工區分自有連結與來源引用。
   rg --hidden -n --glob '!.git/**' --glob '!.serena/**' --glob '!node_modules/**' --glob '!_book/**' 'github\.com/[^/]+/kubernetes-handbook/(blob|tree)/' .
   ```

   歷史來源引用保留可到達的 upstream/tag。原 repo 舊 commit 的內部章節連結若不會存在於新 snapshot，改成目前有效的相對章節連結，或改成明確標示的真實外部來源；不要把舊 SHA 改寫成 `fun-ed` 新 repo 連結。
6. Scanner findings 都已處理或分類，且 staged 檔案已複查後，提交乾淨 snapshot；確認提交樹只含 allowlist。

   ```bash
   git diff --cached --check
   # 整個 snapshot 的 whitespace findings 可能包含繼承自來源的既有內容。
   git diff --cached master --check
   git diff --cached --name-status
   git status --short
   git commit -m "Publish Kubernetes handbook v1.37 upgrade snapshot"
   ```

   clean snapshot 的完整 staged diff 可能揭露來源基線中未改動檔案的既有 whitespace 問題。用 `git diff --cached master --check` 區分本次新增問題與繼承項目，分別報告；不要為此大量重排無關來源內容。

7. 先確認 `origin` 為新 repo 的 HTTPS URL，再設定 GitHub CLI 預設 repo 與本 repo push 預設值。push 時用命令限定的暫時 credential helper；不寫 global credential 設定、不把 PAT/令牌放 URL，不 force push。

   ```bash
   # 前提：new origin 已確認是 https://github.com/fun-ed/kubernetes-handbook.git，且 gh 已登入 fun-ed。
   gh repo set-default fun-ed/kubernetes-handbook
   git config remote.pushDefault origin
   git -c credential.helper= \
     -c credential.helper='!gh auth git-credential' \
     push --set-upstream origin main
   ```

8. 從遠端重新驗證 repo 公開狀態、預設 branch、README、main SHA、local/remote tracking；不能只以 push exit code 當發布完成。

   ```bash
   # 前提：gh、git；在本地 main 分支執行。
   gh repo view fun-ed/kubernetes-handbook --json isPrivate,defaultBranchRef,url
   gh api repos/fun-ed/kubernetes-handbook/commits/main --jq .sha
   git rev-parse HEAD
   git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
   curl -fsSL -o /dev/null -w 'public README HTTP %{http_code}\n' \
     https://raw.githubusercontent.com/fun-ed/kubernetes-handbook/main/README.md
   ```


   接受條件為 `isPrivate=false`、`defaultBranchRef.name=main`、遠端 main SHA 等於本地 HEAD、upstream 是 `origin/main`，且未帶 GitHub 認證的 curl 能讀取 README。若任一不符，記為發布未驗收，不 force push 修復。

## 驗收

升級前完成元件/安全盤點、可還原備份及明確回滾門檻；active 清單逐檔通過 built-in 與 vendor CRD 的 strict server dry-run；目標測試叢集已檢查 API discovery、DNS、網路、儲存、Gateway HTTP/HTTPS、憑證及監控。Go test/vet、文件檢查與 build 按實際執行結果逐項報告，GitBook blocker 明確標受阻。

若執行 publication，公開 repo 的 owner、public visibility、default branch、README、commit SHA 與 upstream tracking 均已核對；clean snapshot 沒有原歷史 ancestry；原本地 branch/remote 仍在；授權和 attribution 保留；secret scanner findings 有逐項分類；沒有 token、`.serena` 私密資料、QA secret 或強制 push。

## 限制

本 SOP 不授權直接操作生產叢集、無人核准的遠端建立/發布、升級後直接降版或清理非本工作資源。Kubernetes/外掛支援範圍依[版本證據矩陣](../setup/component-versions.md)，unknown 不得寫成 supported。GitBook 目前的 installer/plugin 相容性錯誤是已知來源建置 blocker，不能由 QA workaround 推論公開版可成功 render。
