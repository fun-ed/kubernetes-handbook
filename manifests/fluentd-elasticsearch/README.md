# Fluentd + Elasticsearch + Kibana (historical)

The manifests in this directory are a legacy EFK deployment example and are not a current, supported logging stack. They contain old Kubernetes APIs and component assumptions; do not run the old node-labeling, recursive `kubectl apply -f .`, basic-auth, or privileged `sysctl` DaemonSet instructions.

Use a maintained logging backend and its versioned installation instructions for the target Kubernetes release. Review storage, authentication, TLS, node-level permissions, and resource requirements before deployment; this repository does not provide a verified Kubernetes 1.37 replacement. See the [manifests overview](../README.md) for the historical file inventory.
