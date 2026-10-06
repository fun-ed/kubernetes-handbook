# etcd

Kubernetes uses etcd as its consistent key-value store for cluster state. In a standard control plane, the API Server is the component that reads and writes Kubernetes objects in etcd. Kubernetes clients, controllers, and `kubectl` use the Kubernetes API, not etcd's internal storage interface.

For Kubernetes v1.37.1, kubeadm pins etcd v3.7.0. This is a kubeadm default, not a requirement for every distribution; distributions can bundle a different etcd build. See the fixed-version [v1.37.1 dependency list](https://github.com/kubernetes/kubernetes/blob/v1.37.1/build/dependencies.yaml) and the handbook's [version baseline](../../setup/kubernetes-v1.37.md).

## API access and watches

Application clients should list and watch resources through the Kubernetes API. Use the versioned API discovery endpoints or client libraries to determine which resource versions a cluster serves. For large collections, Kubernetes list responses may be paginated with `limit` and `continue`; clients should follow the returned continuation token rather than assume that one response contains the entire collection.

A Kubernetes watch reports changes after a list's resource version. Clients must handle expired resource versions by performing a fresh list, then starting a new watch. Watch streams can disconnect and must be re-established. Do not treat watch as a durable event log. These rules are part of the Kubernetes API contract, not direct etcd watch semantics.

See [API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/), [API discovery](https://kubernetes.io/docs/concepts/overview/kubernetes-api/#api-groups-and-versioning), and the [client-go list/watch guide](https://pkg.go.dev/k8s.io/client-go/tools/cache).

## Operational care

Run etcd as a quorum-based cluster according to the Kubernetes distribution's topology and version guidance. Protect peer and client communication, restrict access to its data directory, and monitor database size, disk latency, quorum health, and defragmentation needs. Back up etcd regularly and verify restore procedures in an isolated environment. Follow the distribution's documented upgrade order; do not independently replace its etcd binaries or change the stored Kubernetes schema.

Use the official [etcd operations guide](https://etcd.io/docs/v3.7/op-guide/) and the distribution-specific backup and recovery instructions. Kubernetes control-plane operators should also consult [Operating etcd clusters for Kubernetes](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/).

## Historical implementation notes

This handbook previously described etcd v2 event history, internal v3 watcher groups, BoltDB record layout, fixed quota defaults, and old utilities. Those implementation details and their limits vary by etcd release and are not Kubernetes API guarantees. The old analysis is retained in the [historical archive](https://github.com/fun-ed/kubernetes-handbook/blob/main/archive/concepts/components/etcd-legacy-analysis.md); use the release-specific etcd documentation for current internals.
