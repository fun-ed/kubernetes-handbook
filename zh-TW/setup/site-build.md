# 網站建置與預覽

本書使用本地 HonKit 6.2.2 建置靜態網站。工具鏈固定為 Node.js 24.21.0 和提交到儲存庫的 `package-lock.json`。不需要全域性安裝 GitBook、HonKit 或外掛，也不要執行舊版 `gitbook install`。

## 前置條件與安裝

需要 Git、mise 或能提供 Node.js 24.21.0 的版本管理器，以及 npm 11.19.0。儲存庫根目錄的 `.nvmrc` 固定 Node 版本。使用 mise 時：

```sh
mise install node@24.21.0
mise exec node@24.21.0 -- npm ci
```

`npm ci` 按 lockfile 安裝 HonKit、外掛與傳遞依賴。依賴版本不一致時，先檢查 Node、npm 與 `package-lock.json`，不要改用全域性安裝來繞過問題。

## 常用命令

```sh
make build
make serve
npm test
npm run check:book
```

`make build` 生成 `_book/`；`make serve` 在本機 `127.0.0.1` 啟動預覽伺服器，預設使用連接埠 4000，預覽和實時過載監聽都限制在迴環介面。`npm test` 執行本地渲染配接器與輸出檢查器的單元測試。`npm run check:book` 檢查已生成的網站檔案、章節內容、導航、搜尋索引、圖片與錨點。先建置再執行輸出檢查。

HonKit 內建程式碼高亮繼續處理程式碼圍欄。Mermaid 圖表由儲存庫本地配接器將圍欄轉換為圖表節點，再呼叫固定版本的本地 `mermaid@12.1.0` 瀏覽器包渲染；只有含圖表的頁面才載入該包，不使用 CDN。配接器顯式設定 `securityLevel: "strict"`。網站使用 HonKit 預設主題，不替換主題。

本書繼續固定穩定版 `gitbook-plugin-search-plus` 1.0.3，以保留它支援的任意字元與程式碼內容搜尋；`book.json` 關閉預設 `search`、`lunr` 外掛。不要改用 `latest` 預釋出版。`editlink` 保留逐頁編輯連結；預設主題側欄提供儲存庫連結。舊 `github` 外掛不再載入。儲存庫配接器保留頁內目錄，把 README 與版本記錄中未列入 `SUMMARY.md` 的 `.agents/` 原始檔連結改為 GitHub 原始碼連結，並在 HonKit 完成網站輸出時恢復 `SUMMARY.md` 的九個原始錨點。未啟用的 `alerts`、`github-buttons` 和 `page-treeview` 依賴已移除。

舊 `page-toc` 外掛只宣告 GitBook 3 相容範圍。儲存庫配接器用預設主題資源提供簡潔的頁內目錄；書籍主導航仍由 `SUMMARY.md` 和預設主題處理。

建置命令先檢查模板塊，再啟動 HonKit。根目錄當前 Markdown 沒有 `{% ... %}` 形式的 GitBook 模板塊。若發現不支援的 hint、tabs、content-ref、file 或 embed 塊，建置會在渲染前失敗並給出路徑。新增這類內容前，先改成 HonKit 支援的 Markdown/HTML，或補上並測試明確的渲染配接器；保留標籤但不顯示內部內容不算相容。

預設主題不做替換。HonKit 原生渲染圖片、表格、程式碼圍欄和普通 Markdown 連結；其預設目錄模板會丟棄 `SUMMARY.md` 標題中的原始 `<a id>`。本地外掛在每次網站生成完成後，把九個 ID 放回對應的側欄標題，並處理 `honkit serve` 的重建。`check:book` 會驗證生成的導航錨點。

## 安全限制

當前鎖定依賴的 `npm audit` 仍報告 9 個 high-severity findings。HonKit 6.2.2 的傳遞依賴鏈中包括 `chokidar`、`nunjucks` 與 `braces`；審計沒有為 HonKit、這些依賴提供可直接採用的相容自動修復，因此此工具鏈不能稱為 audit-clean。Mermaid 的舊外掛依賴已移除；當前鎖定的 Mermaid 將 DOMPurify 解析為 3.4.16，審計未報告 critical finding。升級依賴前應重新審查完整審計結果；只在受信任機器上預覽，並保持 `make serve` 的迴環綁定。


## EPUB、PDF 與 MOBI

```sh
make epub
make pdf
make mobi
```

EPUB 由 HonKit 本地生成。PDF 和 MOBI 轉換需要外部 Calibre 提供 `ebook-convert`。Calibre 不由 npm 安裝或鎖定，CI 只建置網站，不生成這些格式。若轉換失敗，先確認 Calibre 已安裝並可從 `PATH` 找到；不要把缺少 Calibre 當成 HonKit 網站建置失敗。

## 回復

如需回復本次工具鏈，恢復 `Makefile`、`package.json`、`package-lock.json`、`book.json`、`.nvmrc`、`plugins/handbook-rendering/`、`scripts/serve-loopback.cjs` 與 `.github/workflows/docs.yml` 到遷移前版本，並恢復舊的 GitBook CLI 安裝說明。舊 GitBook 3 建置在本儲存庫曾遇到外掛安裝錯誤和 `gitbook-plugin-github@3.0.0` 要求 GitBook 4 alpha 的版本衝突；回復只還原舊設定，不代表舊建置已修復或可用。

## 本次工具鏈驗收（2026-10-05）

固定 Node 24.21.0 的 `npm ci`、12 個配接器／失敗路徑測試、完整 `make build` 和 `npm run check:book` 均透過。網站生成 186 頁，輸出檢查覆蓋程式碼、表格、導航、搜尋索引、圖片與九個原始目錄錨點。

真實瀏覽器還驗證了首屏頁內目錄、搜尋結果和 GitHub 編輯目標；獨立的臨時 Markdown fixture 經 HonKit 建置後，由本地 Mermaid 12.1.0 渲染為 SVG，執行設定為 strict。fixture 未加入手冊章節，也未保留在最終網站產物中。

實際啟動預覽後檢查 TCP listeners，確認網站和實時過載均只監聽 `127.0.0.1`。檢查發現 CLI 傳入數字字串連接埠時，會繞過原先僅測試整數連接埠的限制；現已規範化數字連接埠，並新增對應測試。該限制只作用於預覽命令，不修改全域性 Node 設定。

本節不表示網站已部署、GitHub Actions 已在遠端執行，或 EPUB／PDF／MOBI 已完成驗收。依賴審計仍有上方列明的 9 個 high findings，不能稱為安全審計全透過。
