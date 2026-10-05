# Prometheus manifests (historical)

The files in this directory are an old Prometheus Operator/Ingress example. Its archived chart commands and NGINX Ingress resources are not a supported installation path; do not run them or recursively apply this directory.

For current monitoring, use a maintained Prometheus or Prometheus Operator release and verify its Kubernetes compatibility and installation guidance directly with that project. This repository does not pin a Prometheus stack verified for Kubernetes 1.37. The separate [Metrics Server manifests](../metrics-server/) provide resource metrics for autoscaling and `kubectl top`; they are not a replacement for Prometheus monitoring.

See the [manifests overview](../README.md) for the files classified as historical and current.

