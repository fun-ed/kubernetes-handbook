# Devops

Kubernetes 生态中的 Devops 工具实践。

## 源码部署（Source to Deployment）

- [Draft](draft.md)：当前 Azure Draft CLI 可生成部署文件并创建 GitHub Actions 工作流；旧版 `draft init` / `draft up` 教程见页面内历史说明
- [Skaffold](skaffold.md)：本地 Kubernetes 开发循环，按固定版本下载 CLI
* Metaparticle：提供了一套用于开发云原生应用的标准库，使用方法见 [https://metaparticle.io](https://metaparticle.io)

## CI/CD

- Jenkins X：旧版 1.x 教程已移至[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/apps/devops/jenkinsx.md)；当前状态与部署方式请查阅 [Jenkins X 官方文档](https://jenkins-x.io/)
- [Spinnaker](spinnaker.md)：当前项目状态与官方资料；旧 Helm 2 chart 安装步骤已移至[历史归档](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/apps/devops/spinnaker.md)
- [Argo Workflows](argo.md)
- [Argo CD](argo-cd.md)
- [Flux GitOps](flux.md)

## 其他

- [Kompose](kompose.md)：Compose 转换工具，不要未审查就部署生成的资源

