# Pod egress SNAT 與 IP masquerading

Pod 出站流量的 SNAT 行為由叢集網路實現和雲平台設定共同決定；Kubernetes 核心並未提供一套適用於所有 CNI 的通用安裝步驟。變更 masquerade/SNAT 前，先確認 Pod、Service 和節點網段、流量出口、返回路由，以及由 CNI、節點規則還是雲網路負責轉換。按照所選網路外掛和平台針對目標版本的官方文件設定，並在測試環境驗證。

- [Kubernetes 網路模型](https://kubernetes.io/docs/concepts/services-networking/)
- [Kubernetes SIG Network 的 ip-masq-agent 專案](https://github.com/kubernetes-sigs/ip-masq-agent)
- [Calico 網路文件](https://docs.tigera.io/calico/latest/networking)

> **歷史說明：** 舊版本頁使用了 `kubernetes-incubator/ip-masq-agent` 的 `master` manifest、`beta.kubernetes.io/masq-agent-ds-ready` 標籤及 2018 年的 iptables/CNI 範例。不要將舊 YAML、標籤或 Windows CNI 設定用於 v1.37.1；按當前專案釋出說明和實際 CNI/平台支援矩陣選擇並固定版本。`ip-masq-agent` 是獨立網路元件，不是 Kubernetes v1.37 內建外掛。

排查時比較 Pod 出口前後的源位址，檢查節點上的實際 SNAT 規則和路由，並確認返回路徑。避免在不知道規則所有者和作用範圍時直接修改節點防火牆或 NAT 規則。
