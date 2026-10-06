# Minikube 網路入口

> **舊版實驗，不是 Kubernetes v1.37.1 部署指南。** 本頁原例依賴 Minikube 的 ingress addon、已歸檔的 ingress-nginx、舊 `extensions/v1beta1` Ingress schema，以及 `xip.io` 動態 DNS；舊命令和範例輸出已移除。

Minikube 中 `Service` 型別 `LoadBalancer` 不會自動建立雲廠商負載平衡器。要使用本地 Gateway/Ingress 控制器，應按所選控制器的版本化相容矩陣部署，並選擇受控的本地存取方式（例如 Minikube 支援的 tunnel 或 NodePort）。[Traefik + Gateway API 範例](service-discovery-and-load-balancing.md)固定了 Traefik chart 和與之匹配的 Gateway API CRD 版本；它不會自動為 Minikube 設定外部 DNS 或公網入口。

Minikube addon 與控制器版本由 Minikube 發行版維護；不要假定 `minikube addons enable ingress` 一定安裝受支援的控制器。檢查實際 addon manifest 和其上游維護狀態，避免在新叢集啟用已歸檔的 ingress-nginx。

參考：[Minikube 官方文件](https://minikube.sigs.k8s.io/docs/)、[Kubernetes Service LoadBalancer](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer)、[Kubernetes Gateway API](https://gateway-api.sigs.k8s.io/)。
