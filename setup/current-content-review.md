# 当前内容更新复核

本次复核以 Kubernetes **v1.37.1** 为基线，以 v1.36、v1.37 为比较范围，资料截点为 **2026-10-05**。起始清单列出 176 篇规范 Markdown 文件；另核对了新发现的证书管理指南、代码与清单文件、镜像引用、繁体中文对应页和根目录导览。逐文件路径、复核结果、归档映射和版本证据见[机器可读复核清单](current-content-review.json)。繁体中文版本见[台湾繁体版复核记录](https://github.com/fun-ed/kubernetes-handbook/blob/main/zh-TW/setup/current-content-review.md)。

## 复核范围

各领域负责人分别复核基础概念与组件、部署和扩展、工作负载、网络与排错、示例和组件清单。根目录另复核 `README.md`、`SUMMARY.md`、`CHANGELOG.md`、`plugins/index.md` 及维护 SOP。`zh-TW/coverage.json` 逐项列出现行 Markdown 对应页、排除理由、归档内容和资源文件；旧原文被新指南替换时仍列为当前内容，并另外记录归档副本。
当前 strict Markdown 检查共扫描 359 篇：178 对现行中文文章（356 篇）及根目录的 3 篇治理文件（`AGENTS.md`、`CODE_OF_CONDUCT.md`、`CONTRIBUTING.md`）。这 3 篇不属于繁体中文翻译范围；英文 `en/` 与归档内容也不计入现行文章配对清单。

`archive/index.md` 保留原有 100 条整页归档记录及 Azure GPU 历史片段记录，并补充新归档的非 Markdown 样例、当前页面重写映射和拆出的历史片段。归档由 `.bookignore` 排除，不属于当前书籍导航或当前清单校验范围。

## 已修正的当前内容

- 移除或更正过期 API、旧版控制器配置、过时的运行时参数、失效安装步骤和未经限制的权限或凭据示例。保留历史原文供追溯，不把它们当作当前部署指引。
- 把当前 Kubernetes 资源行为与特定发行版、控制器或云端服务的功能分开说明。未找到 v1.37 支持声明的组件明确标为未知；没有从新版本号推定相容性。
- 更新负载均衡、Service、EndpointSlice、HPA 指标、CSI、节点排错和平台限制说明。移除了通用的公开 RDP `LoadBalancer` 示例，并将旧 Windows 与网络实验清单移出当前路径。
- 修复集群排错页 DNS 命令示例缺少结束围栏、导致后续 Dashboard 与 HPA 章节落入代码块的结构问题。补正指标 API 范围：Kubernetes 的 `metrics.k8s.io/v1` 已稳定，但基线 Metrics Server v0.9.0 与 Kubernetes v1.37.1 HPA 使用 `metrics.k8s.io/v1beta1`；`kubectl top` 可从 v1 回退到 v1beta1。另补充 APIService、aggregation 与指标采集链路的排查边界。
- 全面核对当前文章中的镜像引用：252 个 `image:`／`--image` 出现项，29 个不同值。已核对标签存在性的条目、教学占位符、用户设定变量、需进一步核对的外部引用及可变标签分开记录。已发现并修正过期 NGINX 与 Go 建置镜像；CUDA 教学样例保留其 CUDA 版本语境，没有在上游标签查询受限时猜换版本。标签存在不代表组件受 Kubernetes v1.37 支持。
- 逐项静态盘点 `examples/` 与 `manifests/` 下 65 个非 Markdown 文件，提取到 108 个 API 资源描述。该盘点不等同 API Server、CRD、控制器或工作负载运行验证。

## 版本证据与限制

Kubernetes API 与依赖版本以 [v1.37.1 上游标签](https://github.com/kubernetes/kubernetes/tree/v1.37.1)、[版本弃用指南](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)和[依赖清单](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml)核对。第三方组件的版本、支持声明和相容性证据按组件分别记录在[元件版本清单](component-versions.md)和机器可读复核清单中。

报告不宣称所有组件、云端平台、CNI／CSI 驱动、Windows 节点或生产环境均获 v1.37 支持。没有厂商兼容矩阵或现场环境时，实际运行状态仍未知。镜像标签核验也不等于 digest 固定、架构验证或端到端部署认证。

## 验证状态

内容负责人没有自行运行测试、构建、lint、格式化、安装器、集群或云端命令。以下是主整合者实际运行的检查结果；机器可读复核清单保存了逐项范围和结果。

* Python 内容测试 53 项、npm 测试 12 项、Go informer 回归测试 3 项通过；另有 5 个 CRD 验证库回归案例通过（1 个有效对象接受，4 个无效对象拒绝）。
* 独立清单检查覆盖 54 个 YAML 文件、108 个资源对象；91 个内建资源通过 schema 验证，17 个自定义资源未在本机验证。
* 当前文章内联检查扫描 359 篇 Markdown 和 384 个 YAML fence，共处理 326 个内建资源对象：316 个通过严格 JSON Schema 验证，10 个 CRD 通过 Kubernetes v1.37.1 官方 Go 验证库。另有 26 个自定义资源和 8 个原生配置对象未验证，42 个纯资料文档及 0 个范本不纳入对象验证；执行的验证没有错误。Go 验证库不等于 API server dry-run。
* 只读检查 26 个组件的上游更新状态，执行 85 次请求、0 次请求错误；截至资料截点，没有发现比清单基线更新的稳定版。这不证明任何组件获 Kubernetes v1.37 支持。

最终建置、渲染和输出链接检查结果见机器可读复核清单；本次没有运行 GitHub Actions、API server、集群或云端部署验证。以上检查通过不构成生产环境兼容性声明。

历史升级记录仍见[变更历史](../CHANGELOG.md)和[v1.37.1 适配指南](kubernetes-v1.37.md)。历史记录保留原日期和当时测试范围，不代表本次新增检查结果。
