# 服務治理

本章介紹 Kubernetes 服務治理，包括容器應用管理、Service Mesh 以及 Operator 等。

目前最常用的是手動管理 Manifests，比如 kubernetes github 程式碼庫就提供了很多的 manifest 範例

* [https://github.com/kubernetes/kubernetes/tree/master/cluster/addons](https://github.com/kubernetes/kubernetes/tree/master/cluster/addons)
* [https://github.com/kubernetes/examples](https://github.com/kubernetes/examples)
* [https://github.com/kubernetes/contrib](https://github.com/kubernetes/contrib)
* [https://github.com/kubernetes/ingress-nginx](https://github.com/kubernetes/ingress-nginx)

手動管理的一個問題就是繁瑣，特別是應用複雜並且 Manifest 比較多的時候，還需要考慮他們之間部署關係。Kubernetes 開源社群正在推動更易用的管理方法，如

* [一般準則](patterns.md)
* [滾動升級](service-rolling-update.md)
* [Helm](helm.md)
* [Service Mesh](service-mesh.md)
* [Linkerd 狀態與評估](linkerd2.md)
* [Istio 安裝](../istio/istio-deploy.md)
* [Istio 排錯](../istio/istio-troubleshoot.md)
* [Istio 社群](../istio/istio-community.md)
* [Devops](../devops/)
  * [Draft](../devops/draft.md)
  * [Jenkins X](../devops/jenkinsx.md)
  * [Spinnaker](../devops/spinnaker.md)
  * [Kompose](../devops/kompose.md)
  * [Skaffold](../devops/skaffold.md)
  * [Argo](../devops/argo.md)
  * [Flux GitOps](../devops/flux.md)

已退役的 Linkerd 1.x、舊 CoreOS Operator 和早期 Istio Mixer/API 教程已移入[歷史歸檔](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/index.md)。保留的 Istio 安裝頁面也明確說明 v1.37 相容性尚未得到官方確認。
