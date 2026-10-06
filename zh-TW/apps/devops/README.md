# Devops

Kubernetes 生態中的 Devops 工具實踐。

## 原始碼部署（Source to Deployment）

- [Draft](draft.md)：當前 Azure Draft CLI 可生成部署檔案並建立 GitHub Actions 工作流；舊版 `draft init` / `draft up` 教程見頁面內歷史說明
- [Skaffold](skaffold.md)：本地 Kubernetes 開發迴圈，按固定版本下載 CLI
* Metaparticle：提供了一套用於開發雲原生應用的標準庫，使用方法見 [https://metaparticle.io](https://metaparticle.io)

## CI/CD

- Jenkins X：舊版 1.x 教學已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/apps/devops/jenkinsx.md)；目前狀態與部署方式請查閱 [Jenkins X 官方文件](https://jenkins-x.io/)
- [Spinnaker](spinnaker.md)：目前專案狀態與官方資料；舊 Helm 2 chart 安裝步驟已移至[歷史封存](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/zh-TW/apps/devops/spinnaker.md)
* [Argo](argo.md)
* [Flux GitOps](flux.md)

## 其他

- [Kompose](kompose.md)：Compose 轉換工具，不要未審查就部署生成的資源
