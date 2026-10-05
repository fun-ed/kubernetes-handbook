# Metrics API and metrics-server

metrics-server collects short-lived resource metrics from kubelets and exposes the Kubernetes Metrics API, primarily for `kubectl top` and resource-metric-based HPA. It is not a long-term monitoring or time-series database.

## Install metrics-server 0.9.0

As of 2026-10-05, the upstream stable release is **0.9.0**. Its compatibility matrix lists Kubernetes 1.34 and newer. Check kubelet connectivity and certificates, then apply the versioned upstream manifest:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.0/components.yaml
kubectl -n kube-system rollout status deployment/metrics-server
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl get --raw /apis/metrics.k8s.io
kubectl top nodes
kubectl top pods -A
```

Sources: [v0.9.0 release](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.9.0) and the [upstream installation and compatibility matrix](https://github.com/kubernetes-sigs/metrics-server#readme). Review the upstream certificate, kubelet TLS, network and HA requirements; do not disable TLS verification or copy old Docker firewall changes to make an APIService appear healthy.

## Metrics API version

The Kubernetes API lifecycle and a particular aggregation backend's implementation are separate. A GA `metrics.k8s.io/v1` API does not make the API server convert or provide `v1` when the backend does not serve it. metrics-server 0.9.0's upstream `components.yaml` registers `v1beta1.metrics.k8s.io`, and its compatibility table documents `metrics.k8s.io/v1beta1`. For this deployment, use the version actually advertised by API discovery. If an application requires `v1`, verify that its selected backend explicitly implements and publishes that version first.

```bash
kubectl get --raw /apis/metrics.k8s.io/v1beta1
kubectl get apiservice v1beta1.metrics.k8s.io -o wide
```

For long-term metrics, logs, traces, and alerts, evaluate a monitoring stack instead of Heapster or old metrics-server tutorials.