# 镜像与软件包来源
+
## Kubernetes 官方镜像仓库
+
Kubernetes v1.37 使用 `registry.k8s.io` 发布控制面和官方项目镜像。镜像名应从 Kubernetes 对应版本的部署文档或组件发布材料获取。例如，v1.37.1 kubeadm 使用的 pause 镜像为 `registry.k8s.io/pause:3.10.2`：
+
```bash
crictl pull registry.k8s.io/pause:3.10.2
crictl pull registry.k8s.io/kube-apiserver:v1.37.1
```
+
控制面镜像版本由 Kubernetes 发布和 kubeadm 配置决定，不要仅根据上游组件的最新版本替换。`registry.k8s.io` 下的镜像并非全部由同一个团队维护，部署前请核对该组件的官方版本与支持范围。
+
## Kubernetes 软件包仓库
+
Kubernetes apt/rpm 软件包使用 `pkgs.k8s.io`，每个 Kubernetes minor 版本有单独的软件包仓库。v1.37 的安装步骤和签名密钥见[Kubernetes 官方 kubeadm 安装指南](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)。
+
Debian/Ubuntu 仅需按官方文档添加 v1.37 仓库。下面的 URL 是官方 apt 源；安装前应阅读当前官方指南并验证签名密钥：
+
```text
https://pkgs.k8s.io/core:/stable:/v1.37/deb/
```
+
不要再使用 `apt.kubernetes.io`、`yum.kubernetes.io` 或早期的 Azure 镜像代理作为 Kubernetes 当前软件包来源。旧仓库已经冻结，内容可能随时撤下。
+
## 其他 registry 与镜像代理
+
容器镜像代理、区域 registry 和私有缓存由其运营方维护，不能保证其仍在线、内容完整或与上游同步。部署前应自行确认：
+
- 代理是否允许目标环境访问，且明确支持所需 registry 和镜像路径。
- 拉取的版本或 digest 与上游发布材料一致。
- 代理的认证、TLS、镜像保留和故障恢复策略符合集群要求。
+
不要把未验证的第三方代理改写成公共镜像名称，也不要假设 Docker Hub、GitHub Container Registry、Quay 或云厂商 registry 的镜像路径长期不变。
+
## Helm Chart 来源
+
Helm Charts 可以发布在 OCI registry 或传统 Helm repository。Helm 官方文档推荐使用 Artifact Hub 查找来源；发现 Chart 后应审查维护状态、Chart 版本、容器镜像和 RBAC。旧的 `stable` 与 `incubator` Chart 仓库已不再是 Helm 的当前默认源。
