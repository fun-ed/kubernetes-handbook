# Spinnaker

[Spinnaker](https://www.spinnaker.io/) 是 Google 與 Netflix 釋出的企業級持續交付平臺，具有多雲部署、自動釋出、權限控制以及應用最佳實踐等諸多優點。
> **歷史安裝範例**：本頁中的 `stable/spinnaker` 是已退役的 Helm stable chart 路徑，且 `helm install --name` 是 Helm 2 語法。不要照此部署；Spinnaker 的當前安裝要求和維護狀態以[官方文件](https://spinnaker.io/docs/)為準。

## 部署

```bash
helm install --name spinnaker stable/spinnaker
```
