> HISTORICAL: These source-address descriptions assume old kube-proxy/network-plugin behavior and are not universal. Check the current cluster network and load balancer documentation before relying on them. Preserved from `concepts/objects/service.md`.

## 保留來源 IP

不同類型的 Service 對來源 IP 的處理方式各不相同：

* ClusterIP Service：使用 iptables 模式時，叢集內部的來源 IP 會保留（不進行 SNAT）。如果 client 和 server Pod 位於同一個節點，來源 IP 就是 client Pod 的 IP 位址；如果位於不同節點，來源 IP 則取決於網路外掛程式的處理方式，例如使用 flannel 時，來源 IP 是節點的 flannel IP 位址。
* NodePort Service：預設會對來源 IP 進行 SNAT，server Pod 看到的來源 IP 是節點 IP。若要避免這種情況，可以為 Service 設定 `spec.ExternalTrafficPolicy=Local`（1.6-1.7 版本設定 Annotation `service.beta.kubernetes.io/external-traffic=OnlyLocal`），讓 Service 只代理本機 endpoint 的要求（若沒有本機 endpoint，則直接丟棄封包），藉此保留來源 IP。
* LoadBalancer Service：預設會對來源 IP 進行 SNAT，server Pod 看到的來源 IP 是節點 IP。設定 `service.spec.ExternalTrafficPolicy=Local` 後，可以自動從雲端平台的負載平衡器中移除沒有本機 endpoint 的節點，藉此保留來源 IP。
