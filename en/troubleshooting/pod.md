# Troubleshooting Pods

Start with the Pod's current state, events, and container logs:

```bash
kubectl describe pod -n <namespace> <pod-name>
kubectl logs -n <namespace> <pod-name> -c <container-name>
```

These examples use Kubernetes and CRI terminology. Kubernetes v1.37 does not use the old dockershim integration, and PodSecurityPolicy was removed in v1.25; current Pod admission policy is typically configured with Pod Security Admission or another policy controller.

## Pod stuck in Pending

Pending means the Pod has not been scheduled or cannot yet proceed. `kubectl describe pod` events often report the reason. Check unsatisfied CPU/memory/device requests, taints and tolerations, node selectors/affinity, storage binding, quotas, and whether any node is Ready. Compare the Pod's requests with node allocatable capacity before changing limits or adding nodes.

## Pod stuck in ContainerCreating

Inspect events for image pull, volume mount, sandbox creation, and CNI/IPAM errors:

```bash
kubectl describe pod -n <namespace> <pod-name>
kubectl get pod -n <namespace> <pod-name> -o wide
kubectl describe node <node-name>
```

If the event reports sandbox/network creation failure, use the selected CNI provider's node-agent logs and supported diagnostics; see [network troubleshooting](network.md). If it is a volume issue, inspect the relevant PVC, CSI controller/node plugin and provider events. On the node, follow the installed runtime's instructions for CRI-level diagnosis rather than assuming Docker-specific tooling.

## ImagePullBackOff

Check the event message for an incorrect image reference, inaccessible registry, missing image pull credential, registry rate limit, or node DNS/network issue. Confirm that the image exists for the node's architecture and that any required `imagePullSecrets` are attached to the Pod or ServiceAccount. Avoid placing passwords in shell history or a manifest committed to source control. Use your secret manager to create credentials and follow the registry's instructions.

`docker pull` is not a general Kubernetes node diagnostic on v1.37: the node runtime may be containerd or CRI-O, and kubelet pulls images through CRI.

## CrashLoopBackOff

Read the current and previous container logs and inspect restart state, exit code, probes, resource limits and events:

```bash
kubectl logs -n <namespace> <pod-name> -c <container-name>
kubectl logs -n <namespace> <pod-name> -c <container-name> --previous
kubectl describe pod -n <namespace> <pod-name>
```

If an image lacks a shell or the application exits too quickly, use an approved ephemeral-container workflow such as [`kubectl debug`](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/), subject to cluster policy and RBAC.

## Run a command in a running container

Use `kubectl exec` for commands inside the container. This does not provide access to the host node:

```bash
kubectl exec -it -n <namespace> <pod-name> -c <container-name> -- /bin/sh
```

If host-level diagnosis is necessary, first identify the node with `kubectl get pod -o wide`. Use your organization's approved cloud-console or restricted SSH process to inspect host services and kubelet/runtime logs. Do not expose node SSH through a public `LoadBalancer` Service.

## Pod stuck in Terminating or Unknown

First determine whether the node is reachable and the Pod's controller, storage and volume attachments are healthy. Recovering a disconnected node is safer than forcing deletion when workloads may still be running there. Force deletion can leave the old process alive and cause duplicate writers or data loss, especially for StatefulSet workloads; use it only after verifying the node is stopped or isolated and following the workload's recovery plan.

Do not remove finalizers blindly: they may be responsible for detaching storage or cleaning external resources. Identify the owning controller and use its documented cleanup process.

## Admission rejection or Pod stuck in Error

Read API admission and Pod events. Common causes include missing ConfigMaps/Secrets/PVCs, quota or limit violations, RBAC denial, or rejection by Pod Security Admission or another policy. `PodSecurityPolicy` is a removed API and must not be used for new clusters.

For schema and admission validation without persisting a resource, use server-side dry-run:

```bash
kubectl apply --dry-run=server -f <manifest.yaml>
```

## Static Pods

kubeadm control-plane components are commonly managed as static Pods from `/etc/kubernetes/manifests`. Inspect kubelet status and logs before changing these files; a malformed static Pod manifest can stop a control-plane component. Follow the kubeadm or distribution's documented reconfiguration procedure rather than editing generated manifests as an ad hoc fix.

## References

- [Troubleshoot applications](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-application/)
- [Debug a running Pod](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/)
- [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [API deprecation guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)
