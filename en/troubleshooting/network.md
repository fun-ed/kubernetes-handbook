# Troubleshooting Network

Kubernetes networking depends on the host network, a CNI plugin, Services, and the API/control-plane path. Diagnose the failing layer before changing routes or firewall rules. Commands below are read-only unless otherwise noted.

> This page replaces old kube-dns, Docker FORWARD-policy, mutable `master` manifest, and hand-edited CNI IPAM examples. Kubernetes v1.37 requires a CRI-compatible runtime and a supported CNI provider. Do not disable SELinux or delete IPAM state as a general-purpose fix.

## Pod stuck in ContainerCreating or cannot get an IP

Start with the Pod events, target node and its conditions:

```bash
kubectl describe pod -n <namespace> <pod-name>
kubectl get pod -n <namespace> <pod-name> -o wide
kubectl describe node <node-name>
kubectl get pods -A -o wide --field-selector spec.nodeName=<node-name>
```

Check whether the selected CNI's node agent is ready on that node, then inspect that provider's logs and release-specific diagnostics:

```bash
kubectl get pods -A -o wide | grep -iE 'calico|cilium|flannel|cni'
kubectl -n <cni-namespace> describe pod <cni-node-pod>
kubectl -n <cni-namespace> logs <cni-node-pod> -c <container> --tail=100
```

Confirm the Pod CIDR does not overlap node, service, VPC/VNet, VPN, or other routed CIDRs. Check CNI IP pool capacity, IPAM health, cross-node firewall rules, required tunnel/encapsulation ports, kernel settings, and node routes in the provider's documentation. CNI configuration and IPAM stores are provider-specific. **Do not stop kubelet and delete files from a CNI IPAM directory by hand**; that can allocate duplicate addresses and disrupt running workloads. Escalate exhaustion or suspected IPAM bugs using the plugin's supported recovery procedure.

## DNS lookup failures

kubeadm installs CoreDNS (the `kube-dns` Service name remains for compatibility). DNS depends on the CNI being healthy. Check Pods, logs, Service and EndpointSlices:

```bash
kubectl -n kube-system get pods -l k8s-app=kube-dns -o wide
kubectl -n kube-system logs deployment/coredns --tail=100
kubectl -n kube-system get service kube-dns
kubectl -n kube-system get endpointslices -l kubernetes.io/service-name=kube-dns
```

If CoreDNS is not Ready, inspect its events and Corefile, then confirm that it can reach the cluster API and configured upstream resolvers. Check node routing, firewall policy, CNI health, NetworkPolicy and the host resolver configuration. Do not re-create the kube-dns Service or apply a different DNS deployment to a kubeadm cluster without first comparing it with kubeadm's existing objects.

## Service is not reachable

Check the Service selector, matching Ready Pods, target port, and current EndpointSlices:

```bash
kubectl get service -n <namespace> <service-name> -o yaml
kubectl get pods -n <namespace> --show-labels
kubectl get endpointslices -n <namespace> \
  -l kubernetes.io/service-name=<service-name> -o wide
```

An empty EndpointSlice usually points to a selector mismatch or no Ready backends. If endpoints exist, verify that the application listens on the target port and that NetworkPolicies allow the traffic. Then inspect the installed service dataplane: kube-proxy mode (iptables, nftables, or IPVS where still used), an eBPF replacement, and provider-specific rules are not interchangeable. Do not expect one fixed `iptables-save` chain layout on every Kubernetes v1.37 cluster.

## A Pod cannot reach the API server

First check the in-cluster Kubernetes Service and its EndpointSlices from an administrator context:

```bash
kubectl get service kubernetes
kubectl get endpointslices -l kubernetes.io/service-name=kubernetes
kubectl get --raw='/readyz?verbose'
```

A timeout points toward routing, firewall, CNI or API-server availability. A `403 Forbidden` response instead indicates that the request reached the API but the identity lacks authorization. Check the workload's ServiceAccount and the minimum Role/ClusterRole binding it actually needs; do not grant `cluster-admin` just to suppress a 403.

For control-plane diagnostics, inspect API server Pod status and logs on kubeadm clusters:

```bash
kubectl -n kube-system get pods -l component=kube-apiserver
kubectl -n kube-system logs <apiserver-pod> --tail=100
```

## Reference

- [Debug Services](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-service/)
- [Troubleshoot applications](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-application/)
- [Cluster networking](https://kubernetes.io/docs/concepts/cluster-administration/networking/)
- [Container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [CNI/network plugin guidance](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/)
