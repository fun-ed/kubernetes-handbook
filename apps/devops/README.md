# Devops

Kubernetes 生态中的 Devops 工具实践。

## 源码部署（Source to Deployment）

- [Draft](draft.md)：当前 Azure Draft CLI 可生成部署文件并创建 GitHub Actions 工作流；旧版 `draft init` / `draft up` 教程见页面内历史说明
- [Skaffold](skaffold.md)：本地 Kubernetes 开发循环，按固定版本下载 CLI
* Metaparticle：提供了一套用于开发云原生应用的标准库，使用方法见 [https://metaparticle.io](https://metaparticle.io)

## CI/CD

- Jenkins X：本目录保留的是 Jenkins X 1.x 历史安装流程，不能按当前产品说明执行，见 [Jenkins X 官方文档](https://jenkins-x.io/)
- Spinnaker：旧章中的 `stable/spinnaker` Helm 2 命令已过时，部署方式应以 [Spinnaker 官方文档](https://spinnaker.io/docs/)为准
* [Argo](argo.md)
* [Flux GitOps](flux.md)

## 其他

- [Kompose](kompose.md)：Compose 转换工具，不要未审查就部署生成的资源

