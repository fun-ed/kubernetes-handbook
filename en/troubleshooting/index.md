# Kubernetes Troubleshooting

This is a partial English reference. Current Kubernetes v1.37.1 deployment instructions are in the [Chinese setup guide](../../setup/index.md). Diagnose the API, node, workload, storage, network, and provider layers separately; don't assume every cluster runs kube-proxy in iptables mode or uses the same runtime.

- [Troubleshoot a cluster](cluster.md)
- [Troubleshoot Pods](pod.md)
- [Troubleshoot networking](network.md)
- [Persistent volumes](pv.md)
- [Azure Disk](azuredisk.md)
- [Azure Files](azurefile.md)
- [Windows containers](windows.md)
- [Cloud providers](cloud.md)
- [Azure](azure.md)
- [Diagnostic tools](tools.md)

## First checks

```bash
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl describe pod -n <namespace> <pod-name>
kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp
```

For container logs, inspect the current and previous instance as appropriate:

```bash
kubectl logs -n <namespace> <pod-name> -c <container-name> --tail=100
kubectl logs -n <namespace> <pod-name> -c <container-name> --previous --tail=100
```

On kubeadm clusters, CoreDNS uses the `k8s-app=kube-dns` label and the `kube-dns` Service name. Use [current CoreDNS diagnostics](cluster.md#coredns-crashloopbackoff-or-dns-failures), not old kube-dns container names or manifests. For host-level kubelet/runtime logs, use your provider's restricted node-access process; systemd unit names and log locations vary by distribution.