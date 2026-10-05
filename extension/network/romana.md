# Romana

> **历史项目，安装示例已移除。** 原教程使用 `romana/romana` 仓库 `master` 中的可变 Kubernetes manifests。本书未核实项目当前稳定版本、维护状态或 Kubernetes v1.37.1 兼容矩阵；不要把旧清单应用到当前集群。


Romana是Panic Networks在2016年提出的开源项目，旨在解决Overlay方案给网络带来的开销。

## 历史 Kubernetes 部署说明

旧教程曾分别描述 kubeadm 和 kops 清单，以及通过 CNI、AWS 路由组件进行设置。原始 manifests 指向可变 `master` 分支，已不作为可复制命令保留。

## 工作原理

![](../../.gitbook/assets/romana%20%282%29.png)

![](../../.gitbook/assets/routeagg%20%282%29.png)

* layer 3 networking，消除overlay带来的开销
* 基于iptables ACL的网络隔离
* 基于hierarchy CIDR管理Host/Tenant/Segment ID

![](../../.gitbook/assets/cidr%20%282%29.png)

## 优点

* 纯三层网络，性能好

## 缺点

* 基于IP管理租户，有规模上的限制
* 物理设备变更或地址规划变更麻烦

**参考文档**

* [http://romana.io/](http://romana.io/)
* [Romana basics](http://romana.io/how/romana_basics/)
* [Romana Github](https://github.com/romana/romana)
* [Romana 2.0](http://romana.readthedocs.io/en/latest/index.html)

