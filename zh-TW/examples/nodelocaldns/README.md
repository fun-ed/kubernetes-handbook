# NodeLocal DNS 快取

這些資訊清單是過往且依特定供應商而異的範例。它們會修改 kubelet 設定並包含具特殊權限的主機作業，因此請勿將其作為通用的 NodeLocal DNS 部署方式，套用至目前的叢集。這些範例需要相符的 CNI 設定，且必須替換 Corefile 中的預留位置。如需目前的指引，請參閱 [Kubernetes DNS 專案](https://github.com/kubernetes/dns)。