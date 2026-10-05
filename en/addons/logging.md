# Cluster logging

Kubernetes does not deploy a centralized log backend or a Fluentd agent on every node by default. Applications commonly write to standard output and standard error; a node-level logging agent can collect those records and forward them to a centralized store and query system. Choose an agent, backend, and deployment method whose current documentation supports your Kubernetes version, node operating system, and container runtime. Review its permissions, retention policy, and data-export requirements.

- [Kubernetes cluster logging architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Kubernetes logging documentation](https://kubernetes.io/docs/tasks/debug/)

> **Historical note:** Earlier versions of this page described `cluster/kube-up.sh`, Fluentd/Elasticsearch/Kibana manifests from the Kubernetes repository, the `beta.kubernetes.io/fluentd-ds-ready` node label, and accessing Kibana through a `kubectl proxy` bound to `0.0.0.0`. Those scripts, labels, and manifests are not a supported Kubernetes v1.37.1 deployment recipe. Do not apply the old manifests or expose an API proxy to untrusted networks. The former ELK overview is retained only as context.

Before deployment, verify the agent's node permissions, RBAC and Secret requirements, network egress, and resource limits. Ensure logs do not collect sensitive information that should not be retained or exported.
