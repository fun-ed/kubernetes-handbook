# 序言

Kubernetes 是 Google 開源的容器叢集管理系統，源自 Google 多年來大規模管理容器的 Borg 專案，也是 CNCF 的重要專案之一。主要功能包括：

* 以容器部署、維護及滾動升級應用程式
* 負載平衡與服務探索
* 跨機器及跨地區排程叢集工作負載
* 自動擴縮
* 支援無狀態及有狀態服務
* 支援多種 Volume
* 透過外掛擴充功能

Kubernetes 發展迅速，已成為容器編排領域的主流平台。中文資料雖然豐富，具系統性且持續跟進社群更新的資源仍然較少。《Kubernetes 指南》整理開發及使用 Kubernetes 時的參考資訊與實務經驗，方便讀者查閱。

## 線上閱讀

* [台灣繁體中文版目錄](https://github.com/fun-ed/kubernetes-handbook/blob/main/zh-TW/SUMMARY.md)
* [GitHub 專案原始碼](https://github.com/fun-ed/kubernetes-handbook)

本專案尚未部署獨立的 GitBook 網站；線上閱讀請使用本版本目錄或 GitHub 上的文件。

## 專案與授權

本書由 **fun-ed** 以 **Pengfei Ni 及原專案貢獻者**的 [Kubernetes Handbook 原著](https://github.com/feiskyer/kubernetes-handbook)為基礎維護，保留原作者署名及 CC BY-NC-SA 4.0 授權。本次發布採用整理後的內容快照，不包含原始碼庫的歷史提交。

## 版本與維護

本指南以 **Kubernetes v1.37.1** 為部署基準，元件版本快照截至 **2026-10-05**。升級前請閱讀 [v1.37 相容性指南](setup/kubernetes-v1.37.md)、[元件版本清單](setup/component-versions.md)及[版本支援策略](setup/upgrade.md)。

以 v1.37 為最新分支時，官方維護 v1.37、v1.36、v1.35；這與各元件允許的版本偏差不同。對應版本表見 [Kubernetes 簡介](introduction/index.md)的「Kubernetes 版本」一節。

舊版教學及資源已移至[封存區](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/README.md)，供歷史參考，不是目前的安裝指南。舊版 API、啟動參數、退役元件及雲端平台步驟不能只替換版本號後直接使用。元件發布了新版本，也不代表該版本已通過 Kubernetes v1.37 相容性驗證。詳細變更請參閱 [CHANGELOG](https://github.com/fun-ed/kubernetes-handbook/blob/main/CHANGELOG.md)。

本次現行內容檢查的範圍、修正、封存對照與未驗證項目，見[現行內容檢查記錄](setup/current-content-review.md)。

本次升級流程與驗證紀錄：

* [Investigate：版本相容性與支援範圍調查](https://github.com/fun-ed/kubernetes-handbook/blob/main/.agents/skill-investigate.md)
* [Debug：重現問題、蒐集證據與最小修正](https://github.com/fun-ed/kubernetes-handbook/blob/main/.agents/skill-debug.md)
* [Maintenance：升級、驗證、回復與 GitHub 發布](https://github.com/fun-ed/kubernetes-handbook/blob/main/.agents/skill-maintenance.md)

網站建置、最小回歸驗證及版本追蹤分開處理，避免把文件成功建置誤當成元件相容性已驗證：

* [網站建置與預覽](setup/site-build.md)：固定 Node LTS、HonKit 及 npm lockfile，保留既有章節與目錄。
* [最小回歸驗證](setup/verification.md)：本機 strict schema 檢查，以及明確啟用的隔離 kind API／runtime 檢查。
* [相容性追蹤](setup/compatibility-tracking.md)：唯讀檢查上游穩定版；官方支援範圍仍須人工核對，不會自動升級。
* [現行元件與範例版本核對](setup/component-current-status.md)：分開記錄上游最新版、發行版固定值與 YAML 範例；另提供 [k0s](setup/cluster/k0s.md)及 [RKE2](setup/cluster/rke2.md)部署與設定範例。

生成的網站尚未自動部署。公開閱讀入口以本頁上方連結為準。歷史驗證紀錄保留原日期；後續檢查結果以實際執行輸出為準。

## 本機建置

在儲存庫根目錄執行下列命令，可使用專案安裝的 HonKit 建置台灣繁體中文版。網站輸出至 `/tmp`，不會覆寫根目錄的主要版本：

```sh
mise exec node@24.21.0 -- npm exec -- honkit build zh-TW /tmp/kubernetes-handbook-zh-tw-book
```

## 版本涵蓋範圍

本版本涵蓋 `coverage.json` 列出的 188 篇目前內容，並包含本序言與完整目錄。清單納入主目錄未連結、但仍屬目前內容的範例、資訊清單說明、網路主題索引及附錄。封存的 46 篇 Markdown、英文版 `en/`、儲存庫維護規範及封存目錄頁面不納入本版本；排除項目與理由詳列於 `coverage.json`。程式碼範例、API 識別字、命令、URL 與資產檔名均依原文保留。

## 授權

![LICENSE](https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png)

[姓名標示－非商業性－相同方式分享 4.0 國際（CC BY-NC-SA 4.0）](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh)。
