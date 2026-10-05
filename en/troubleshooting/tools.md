# Tools for Troubleshooting

Use tools appropriate to the layer and configuration being inspected. Do not assume a particular service dataplane, Linux distribution, runtime, or package manager.

## Core tools

- `kubectl` for Kubernetes API objects, events, logs, and Pod inspection.
- `journalctl` on Linux nodes for systemd-managed kubelet and runtime services, using restricted provider/administrator access.
- `crictl` for CRI-level inspection when required; install a version compatible with your Kubernetes minor from the [cri-tools project](https://github.com/kubernetes-sigs/cri-tools) and point it at the correct CRI socket.
- `ip`, `ss`, and `tcpdump` for node interface, route, socket, and packet-level diagnosis. Use firewall tooling that matches the host and service dataplane; an eBPF, nftables, or provider-managed path may not produce the legacy iptables chains shown in old examples.
- `perf` or an approved system profiler for host performance investigations; check kernel and security requirements first.

## Sysdig

Sysdig may be useful for host and container observability where it is maintained and approved. Install it only by following the project's current [official installation and verification instructions](https://docs.sysdig.com/en/docs/installation/). The package URLs, `apt-key`, HTTP repository and EPEL commands in the former version of this page are historical and must not be run on current hosts.

## Weave Scope

> **Historical tool:** Weave Scope's old generated `scope.yaml` install command is not a maintained Kubernetes v1.37 deployment path. Do not apply it to a production cluster. The previous content also assumed Docker hosts and a public LoadBalancer.

Choose a maintained observability tool using its current Kubernetes support and security documentation. For the current handbook monitoring option, see [Prometheus monitoring](../../setup/addon-list/monitor.md).
