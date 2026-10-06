# Jenkins X

[Jenkins X](http://jenkins-x.io/) 是一個基於 Jenkins 和 Kubernetes 的 CI/CD 平臺，旨在解決微服務架構下雲原生應用的持續整合和持續交付問題。它使用 Jenkins、Helm、Draft、GitOps 以及 Github 等工具鏈構造了一個從叢集安裝、環境管理、持續整合、持續部署一直到應用釋出等支援整個流程的平臺。
> **歷史版本說明**：本章中的 `jx` v1.1.10、舊 `jx install` 和 Jenkins X 1.x 命令不是當前產品部署說明。不要用於新叢集；請檢視 [Jenkins X 官方文件](https://jenkins-x.io/)確認當前專案狀態、發行版和安裝路徑。

## 安裝部署

### 安裝 jx 命令列工具

```bash
# MacOS
brew tap jenkins-x/jx
brew install jx

# Linux
curl -L https://github.com/jenkins-x/jx/releases/download/v1.1.10/jx-linux-amd64.tar.gz | tar xzv
sudo mv jx /usr/local/bin
```

### 部署 Kubernetes 叢集

如果 Kubernetes 叢集已經部署好了，那麼該步可以忽略。

`jx` 命令提供了在公有云中直接部署 Kubernetes 的功能，比如

```bash
create cluster aks      # Create a new kubernetes cluster on AKS: Runs on Azure
create cluster aws      # Create a new kubernetes cluster on AWS with kops
create cluster gke      # Create a new kubernetes cluster on GKE: Runs on Google Cloud
create cluster minikube # Create a new kubernetes cluster with minikube: Runs locally
```

### 部署 Jenkins X 服務

注意在安裝 Jenkins X 服務之前，Kubernetes 叢集需要開啟 RBAC 並開啟 insecure docker registries（`dockerd --insecure-registry=10.0.0.0/16` ）。

執行下面的命令按照提示操作，該過程會設定

* Ingress Controller （如果沒有安裝的話）
* Ingress 公網 IP 的 DNS（預設使用 `ip.xip.io`）
* Github API token（用於建立 github repo 和 webhook）
* Jenkins-X 服務
* 建立 staging 和 production 等範例專案，包括 github repo 以及 Jenkins 設定等

```bash
jx install --provider=kubernetes
```

安裝完成後，會輸出 Jenkins 的存取入口以及管理員的使用者名稱和密碼，用於登入 Jenkins。

## 建立應用

Jenkins X 支援快速建立新的應用

```bash
# 创建 Spring Boot 应用
jx create spring -d web -d actuator

# 创建快速启动项目
jx create quickstart  -l go
```

也支援匯入已有的應用，只是需要注意匯入前要保證

* 使用 Github 等 git 系統管理原始碼並設定好 Jenkins webhook
* 新增 Dockerfile、Jenkinsfile 以及執行應用所需要的 Helm Chart

```bash
# 从本地导入
$ cd my-cool-app
$ jx import

# 从 Github 导入
jx import --github --org myname

# 从 URL 导入
jx import --url https://github.com/jenkins-x/spring-boot-web-example.git
```

## 釋出應用

```bash
# 发布新版本到生产环境中
jx promote myapp --version 1.2.3 --env production
```

![](../../../.gitbook/assets/jenkinsx%20%281%29.png)

## 常用命令

```bash
# Get pipelines
jx get pipelines

# Get pipeline activities
jx get activities

# Get build logs
jx get build logs -f myapp

# Open Jenkins in brower
jx console

# Get applications
jx get applications

# Get environments
jx get environments
```
