# 序言

[![star this repo](https://badgen.net/github/stars/fun-ed/kubernetes-handbook)](https://github.com/fun-ed/kubernetes-handbook) [![fork this repo](https://badgen.net/github/forks/fun-ed/kubernetes-handbook)](https://github.com/fun-ed/kubernetes-handbook/fork) [![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/fun-ed/kubernetes-handbook/issues)

Kubernetes 是谷歌开源的容器集群管理系统，是 Google 多年大规模容器管理技术 Borg 的开源版本，也是 CNCF 最重要的项目之一，主要功能包括：

* 基于容器的应用部署、维护和滚动升级
* 负载均衡和服务发现
* 跨机器和跨地区的集群调度
* 自动伸缩
* 无状态服务和有状态服务
* 广泛的 Volume 支持
* 插件机制保证扩展性

Kubernetes 发展非常迅速，已经成为容器编排领域的领导者。Kubernetes 的中文资料也非常丰富，但系统化和紧跟社区更新的则就比较少见了。《Kubernetes 指南》开源电子书旨在整理平时在开发和使用 Kubernetes 时的参考指南和实践总结，形成一个系统化的参考指南以方便查阅。欢迎大家关注和添加完善内容。

## 在线阅读

* GitHub: [fun-ed/kubernetes-handbook 在线目录](https://github.com/fun-ed/kubernetes-handbook/blob/main/SUMMARY.md)

本仓库尚未部署独立 GitBook 站点；在线内容以这里的 GitHub 文档为准。

## 项目源码

项目源码存放于 GitHub：[https://github.com/fun-ed/kubernetes-handbook](https://github.com/fun-ed/kubernetes-handbook)。

本仓库由 **fun-ed** 基于 **Pengfei Ni 及原项目贡献者**的 [Kubernetes Handbook 原著](https://github.com/feiskyer/kubernetes-handbook)适配维护，保留原作者署名与 CC BY-NC-SA 4.0 授权。本次发布采用清理后的内容快照，不带入原仓库历史提交；改动与验证范围见下方记录。

### 本书版本更新记录

本指南的当前部署基线为 **Kubernetes v1.37.1**，组件版本快照截止于 **2026-10-05**。升级前请阅读 [v1.37 适配指南](setup/kubernetes-v1.37.md)、[组件版本清单](setup/component-versions.md)和[版本支持策略](setup/upgrade.md)。

本书保留明确标记的历史教程及版本特定示例，它们不代表 v1.37 的可执行部署流程。旧版本的 API、启动参数、已退役组件和云平台步骤不能通过替换版本号直接复用。组件已发布最新版本也不等于已经验证对 v1.37 的兼容性。详细更新记录见 [CHANGELOG](CHANGELOG.md)。

本次升级的 SOP：

* [Investigate：版本、相容性与适配范围调查](.agents/skill-investigate.md)
* [Debug：复现、证据与最小修复](.agents/skill-debug.md)
* [Maintenance：升级、验证、回退与 GitHub 发布](.agents/skill-maintenance.md)

## 原作者微信公众号

以下为原项目保留的作者渠道，不是 fun-ed 仓库的独立发布渠道。

![](.gitbook/assets/wx.png)

## 贡献者

欢迎参与贡献和完善内容，贡献方法参考 [CONTRIBUTING](https://github.com/fun-ed/kubernetes-handbook/blob/main/CONTRIBUTING.md)。本仓库的贡献者列表见 [contributors](https://github.com/fun-ed/kubernetes-handbook/graphs/contributors)；原著贡献者的署名与版权仍予保留。


## LICENSE

![LICENSE](https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png)

[署名-非商业性使用-相同方式共享 4.0 \(CC BY-NC-SA 4.0\)](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh)。
