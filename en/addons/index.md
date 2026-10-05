# Add-ons

Kubernetes does not install every networking, metrics, monitoring, or autoscaling component for you. Check each upstream project's supported Kubernetes matrix and provider-specific instructions before deployment. The maintained installation path in this handbook targets Kubernetes v1.37.1 and is in the [Chinese setup guide](../../setup/index.md).

- [CoreDNS](../../setup/addon-list/kube-dns.md): kubeadm installs it by default; old kube-dns YAML is historical.
- [metrics-server](metrics.md): current upstream v0.9.0 manifest serves `metrics.k8s.io/v1beta1`; this is an immediate metrics API, not long-term monitoring.
- [Monitoring](monitor.md): latest pinned Prometheus community chart and compatibility caveats.
- [Cluster Autoscaler](cluster-autoscaler.md): no verified stable release/compatibility entry for Kubernetes v1.37 as of 2026-10-05; do not deploy the v1.36 release on v1.37 by assumption.
- [Kubernetes Dashboard](dashboard.md): upstream archived the project in January 2026; no current Dashboard install is recommended.
- [GPU workloads](../../setup/addon-list/gpu.md): NVIDIA GPU Operator 26.7.1's 26.7 support matrix covers Kubernetes v1.33–v1.37; still verify the complete platform combination.
- [Logging](logging.md): Kubernetes does not deploy a centralized logging backend or node agent by default.
- [Pod egress SNAT](../../setup/addon-list/ip-masq-agent.md): behavior depends on the selected CNI and cloud platform; do not apply the historical manifest.

The former English pages for Heapster, Dashboard, and old autoscaler releases have been replaced with project status and safe current links.