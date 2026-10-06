# Spinnaker

[Spinnaker](https://www.spinnaker.io/) 是 Google 与 Netflix 发布的企业级持续交付平台，具有多云部署、自动发布、权限控制以及应用最佳实践等诸多优点。
> **历史安装示例**：本页中的 `stable/spinnaker` 是已退役的 Helm stable chart 路径，且 `helm install --name` 是 Helm 2 语法。不要照此部署；Spinnaker 的当前安装要求和维护状态以[官方文档](https://spinnaker.io/docs/)为准。

## 部署

```bash
helm install --name spinnaker stable/spinnaker
```
