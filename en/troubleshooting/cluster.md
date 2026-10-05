# Troubleshooting Kubernetes Cluster

This chapter is about kubernetes cluster (kubernetes service itself) troubleshooting, including issues of kubernetes core components and addons. For network related issues, please refer to [Troubleshooting Network](network.md).

## Overview

If there is something wrong with kubernetes components, the first thing we need to do is identifying which component are abnormal, e.g.

```sh
kubectl -n kube-system get pods
```

Pay attention to pods not in `Running` status or whose restart counts are not zero. After confirmed the ill-behavior components, then we could identify how to fix it. There are a lot of reasons which could result in cluster unhealthy, which include

- VM or physical machine shutdown
- Network partition within cluster, or between clusters
- Crashes in Kubernetes components
- Data loss or unavailability of persistent storage (e.g. GCE PD or AWS EBS volume)
- Operator error, e.g. misconfigured Kubernetes software or application software

Specifically, we could group those reasons by components

- **kube-apiserver VM shutdown or kube-apiserver crashing** could result in
  - unable to stop, update, or start new pods, services, replication controller
  - existing pods and services should continue to work normally, unless they depend on the Kubernetes API
- **etcd cluster down or abnormal** could result in
  - kube-apiserver fails to come up
  - cluster changes to read only
  - kubelet couldn't update its status but will continue to run original Pods
- **kube-controller-manager/kube-scheduler VM shutdown or crash** could result in
  - Deployment and StatefulSet controllers stop reconciling replicas, and unscheduled Pods remain pending.
  - Node controller stops to work and no new node could be registered in the cluster
  - Scheduler is down so that new pods couldn't be scheduled
  - This is why HA is important
- **CoreDNS is unavailable** (kubeadm's DNS Service remains named `kube-dns`), so in-cluster DNS lookups fail and workloads that rely on service discovery may be affected.
- **Individual node (VM or physical machine) shuts down** could result in
  - pods on that Node stop running
- **Network partition** could result in
  - partition A thinks the nodes in partition B are down; partition B thinks the apiserver is down. (Assuming the master VM ends up in partition A.)
  - pods not tolerating partition stop to work
- **Kubelet crash** could result in
  - crashing kubelet cannot start new pods on the node
  - kubelet might delete the pods or not
  - node marked unhealthy
  - replication controllers start new pods elsewhere
- **Cluster operator** error could result in
  - loss of pods, services, etc
  - lost of apiserver backing store
  - users unable to read API

## General mitigations

A general list of mitigtions include

- Use IaaS provider’s automatic VM restarting feature for IaaS VMs
- Use IaaS providers reliable storage (e.g. GCE PD or AWS EBS volume) for VMs with apiserver+etcd
- Configure multiple nodes cluster for etcd and backup data periodically
- Configure high-availability for controller components, e.g.
  - load balancer on front of kube-apiserver
- Build high availability using the supported control-plane and DNS deployment process; do not scale kubeadm static Pods manually.
- Use workload controllers such as Deployments/StatefulSets and Services instead of relying on unmanaged Pods.
- Multiple independent clusters and avoid making risky changes to all clusters at once

## Listing nodes

Normally, all nodes should be in Ready state

```sh
kubectl get nodes
kubectl describe node <node-name>
```

If some nodes are in `NotReady` state, `kubectl describe node <node-name>`  could get the node's events, which usually helps to identify the problem.

## Accessing a Node for diagnosis

For an application container, use `kubectl exec` to run a shell inside the container; this is not a shell on the host:

```sh
kubectl exec -it -n <namespace> <pod-name> -c <container-name> -- /bin/sh
```

For a node's host network context, this repository has a restricted diagnostic [Pod example](../../examples/ssh.yaml). Despite its filename, it does not run sshd or expose a Service. Review the manifest, replace its `nodeName` placeholder, and use it only on a trusted cluster. Its `hostNetwork` setting shares the selected node's network context, but the Pod is not a host shell and does not mount the host filesystem.

From the repository root, apply the edited manifest and enter the shell:

```sh
kubectl apply -f examples/ssh.yaml
kubectl exec -it node-debug-shell -- /bin/sh
kubectl delete -f examples/ssh.yaml
```

For host services or kubelet/runtime logs, use the cloud provider's console or your organization's restricted node-access method; do not create a public `LoadBalancer` for SSH.


## Looking at logs


Components may run as static Pods or systemd services, depending on the distribution. On kubeadm clusters, read control-plane Pod logs through the API while it is available:

```sh
kubectl -n kube-system logs <pod-name> --all-containers --tail=100
```

For host-level kubelet or runtime problems, use the provider's restricted node-access method and consult that Linux distribution's journal/service names, for example:

```sh
journalctl -u kubelet --since=-10m
```

Control-plane static Pods do not necessarily have separate systemd services, and log-file paths vary by runtime and distribution.


### Looking at kube-apiserver logs

Suppose kube-apiserver is running as static pods

```sh
PODNAME=$(kubectl -n kube-system get pod -l component=kube-apiserver -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

### Looking at kube-controller-manager logs

Suppose kube-controller-manager is running as static pods

```sh
PODNAME=$(kubectl -n kube-system get pod -l component=kube-controller-manager -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

### Looking at kube-scheduler logs

Suppose kube-scheduler is running as static pods

```sh
PODNAME=$(kubectl -n kube-system get pod -l component=kube-scheduler -o jsonpath='{.items[0].metadata.name}')
kubectl -n kube-system logs $PODNAME --tail 100
```

### Looking at CoreDNS logs

On kubeadm clusters, inspect the CoreDNS Deployment and current Pod logs:

```sh
kubectl -n kube-system get pods -l k8s-app=kube-dns -o wide
kubectl -n kube-system logs deployment/coredns --tail=100
```

### Looking at kubelet logs

On kubeadm Linux nodes, kubelet normally runs as a systemd service. Use restricted node access and inspect the host journal:

```sh
journalctl -u kubelet --since=-10m
```


### Looking at kube-proxy logs

Suppose kube-proxy is running as daemonset pods

```sh
$ kubectl -n kube-system get pod -l component=kube-proxy
NAME               READY     STATUS    RESTARTS   AGE
kube-proxy-42zpn   1/1       Running   0          1d
kube-proxy-7gd4p   1/1       Running   0          3d
kube-proxy-87dbs   1/1       Running   0          4d
$ kubectl -n kube-system logs kube-proxy-42zpn
```

## CoreDNS CrashLoopBackOff or DNS failures

On kubeadm clusters, CoreDNS Pods use the `k8s-app=kube-dns` label and the Service is named `kube-dns`. Check the Pod state, events, logs, Service, and EndpointSlices:

```sh
kubectl -n kube-system get pods -l k8s-app=kube-dns -o wide
kubectl -n kube-system describe deployment/coredns
kubectl -n kube-system logs deployment/coredns --tail=100
kubectl -n kube-system get service kube-dns
kubectl -n kube-system get endpointslices -l kubernetes.io/service-name=kube-dns
```

If CoreDNS cannot reach an upstream resolver, inspect its Corefile, node routing, host resolver configuration, CNI health, firewall rules and applicable NetworkPolicies. If the API is unreachable, check API server availability and Pod-to-control-plane network paths. Do not apply old kube-dns YAML or the Docker-era `iptables -P FORWARD ACCEPT` workaround. See [network troubleshooting](network.md) and the current [CoreDNS setup notes](../../setup/addon-list/kube-dns.md).

## Node allocatable warnings

If a node reports `FailedNodeAllocatableEnforcement`, inspect the current kubelet configuration, node allocatable values, cgroup version, and kubelet/runtime cgroup-driver agreement. Use the official [node resource reservation guide](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/) and the runtime-specific [cgroup driver documentation](https://kubernetes.io/docs/setup/production-environment/container-runtimes/#cgroup-drivers). The Docker overlay2 log excerpt and `--exec-opt native.cgroupdriver=systemd` advice in older copies of this page described a legacy runtime and are not current fixes.



## kube-proxy reports a missing `conntrack` helper

Older kube-proxy logs can report that the `conntrack` executable is missing. On Kubernetes v1.37, verify the exact runtime, distribution package, kube-proxy configuration and provider guidance before changing node packages or restarting networking. Do not assume that the old `conntrack-tools` installation command applies to every operating system or service dataplane.


## No metrics in a Dashboard

The old Dashboard/Heapster examples are historical: Heapster is retired and the Kubernetes Dashboard project is archived. For `kubectl top` and resource-metric HPA, check the current Metrics API backend and APIService; see [metrics-server setup](../../setup/addon-list/metrics.md). For long-term monitoring, evaluate a maintained monitoring stack rather than installing Heapster.

## HPA does not scale Pods

Inspect HPA conditions and events:

```sh
kubectl describe hpa -n <namespace> <hpa-name>
kubectl get hpa -n <namespace> <hpa-name> -o yaml
```

For CPU or memory resource metrics, check whether the cluster's actual metrics backend is healthy and registered:

```sh
kubectl get apiservice
kubectl get apiservice v1beta1.metrics.k8s.io -o wide
kubectl get --raw /apis/metrics.k8s.io
kubectl top pods -n <namespace>
```

If the APIService is unavailable, inspect the metrics-server Pod events/logs and kubelet connectivity. Kubernetes API version lifecycle does not change a backend's implementation: upstream metrics-server 0.9.0 serves `metrics.k8s.io/v1beta1`, so verify the version reported by API discovery. See [metrics-server setup](../../setup/addon-list/metrics.md).

## References

- [Troubleshoot clusters](https://kubernetes.io/docs/tasks/debug/debug-cluster/)
- [Kubernetes version skew policy](https://kubernetes.io/releases/version-skew-policy/)
- [API deprecation guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)
