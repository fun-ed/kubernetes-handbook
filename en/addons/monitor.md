# Kubernetes monitoring

As of 2026-10-05, the latest stable Prometheus community `kube-prometheus-stack` chart is **91.9.0**, released on 2026-10-02. It packages the Prometheus Operator, Prometheus, Alertmanager, node-exporter, kube-state-metrics and a default Grafana configuration. A current chart release is not, by itself, a claim of certification for Kubernetes v1.37.

With Helm 4.3.0, the version-pinned install command is:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 91.9.0 --namespace monitoring --create-namespace
```

Sources: [chart 91.9.0 release](https://github.com/prometheus-community/helm-charts/releases/tag/kube-prometheus-stack-91.9.0), [chart source and documentation](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack), and [Helm installation and release information](https://helm.sh/docs/intro/install/). Before production use, check the selected chart release's Kubernetes v1.37 and Helm 4 compatibility, CRD changes, storage, resource use, authentication, exposure, and upgrade/rollback notes. This page does not assert an unverified chart compatibility matrix.

metrics-server serves the short-lived Metrics API for `kubectl top` and HPA; it is not a replacement for Prometheus or long-term metrics retention.

> **Historical note:** Heapster is retired and archived. Old Heapster, cAdvisor, Docker daemon flag, Dashboard, and unpinned chart examples from this page are not suitable for v1.37.1; they are not retained as executable instructions.