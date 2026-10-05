# Cluster Autoscaler

Cluster Autoscaler calls cloud-provider or infrastructure APIs to resize node groups. Its configuration, IAM permissions, node templates, and installation are provider-specific; use the provider's maintained deployment guide.

The upstream project recommends matching the Cluster Autoscaler minor version to the Kubernetes control-plane minor. As of 2026-10-05, the latest stable release is **1.36.1**. The upstream compatibility README does not list Kubernetes v1.37, and no stable CA v1.37 release has been verified. Do not deploy CA 1.36.1 on Kubernetes 1.37 merely because it is the latest release; this handbook intentionally gives no v1.37 installation manifest or image pin until upstream publishes a matching release and compatibility entry.

Check the [upstream releases](https://github.com/kubernetes/autoscaler/releases), [compatibility table](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/README.md), and your cloud provider's support matrix before deployment. Old CA 1.0/1.3 manifests and broad cluster-admin examples are not current instructions.