# Kubernetes Examples

These manifests target Kubernetes v1.37.1. They are teaching examples, not a
single installable stack: do not apply the entire directory. Check each
example's comments and prerequisites, then select individual files for a
disposable cluster.

Core Kubernetes component pins and source evidence are tracked in
[`../setup/component-versions.md`](../setup/component-versions.md).

## Validate before applying

For a built-in resource, use a v1.37.1 test cluster and server-side dry-run:

```sh
kubectl --context "$KUBE_CONTEXT" apply --dry-run=server -f examples/deployment.yaml
```

This validates against that cluster's API without persisting the object. It
still requires access to the API and can invoke admission webhooks. Offline
schema validation is also possible with
`kubeconform -strict -kubernetes-version 1.37.1 <manifest>`. Custom resources
need their CRD schemas (or installed CRDs for server-side validation), and
feature-gated examples need the relevant feature enabled. Neither check proves
that a workload's external images, credentials, storage, or services exist.

## Examples with additional requirements

- `hpa.yaml` and `hpa-memory.yaml` target the `nginx` Deployment in
  `deployment.yaml` and require a functioning metrics API, commonly
  metrics-server. The Deployment includes CPU and memory requests.
- `network-policy/` needs a CNI that enforces NetworkPolicy; its access and
  no-access Pods are one-shot connectivity checks.
- `service.yaml` selects Pods labeled `app: nginx`; its second port also
  requires an application listening on container port 8080.
- `indexed-job-with-backoff.yaml` and `job-success-policy-v1.33.yaml` use Job
  features that are stable and enabled by default in v1.37.1.
- `lifecycle-v1.33.yaml` mixes stable lifecycle sleep examples with
  `stopSignal`, which is still alpha in v1.37 and requires the
  `ContainerStopSignals` feature gate. Skip those resources unless the gate is
  enabled on the cluster components that handle Pods.
- `user-namespace.yaml` uses stable Pod user namespaces (`hostUsers: false`,
  stable since v1.36); it requires a Linux cluster that supports user
  namespaces. Its ConfigMap, Secret, PVC, and custom-image examples have
  placeholders or external prerequisites. The PostgreSQL 18 sample stores data
  under `/var/lib/postgresql`.
- `seccomp.yaml` requires the supplied `prevent-chmod` profile at
  `/var/lib/kubelet/seccomp/prevent-chmod` on every eligible node.
- `calico/calico-packet-logs.yaml` is a Calico-specific custom resource and
  DaemonSet: use Calico 3.33.0 with its CRDs and logging configured. Its
  opt-in policy selects only endpoints carrying the `packet-log-demo` label.
  Add that label deliberately before applying it; matching TCP/UDP ingress
  and egress traffic is logged and allowed.
- `service-without-selector.yaml` and `rdp.yaml` demonstrate manual
  EndpointSlices. Replace their documentation-only `192.0.2.10` address with
  an address reachable by clients. `rdp.yaml` also requires a LoadBalancer
  implementation and exposes an RDP endpoint; do not publish it unintentionally.
- `pod-secret.yaml` and `image-scret.yaml` require a real private registry and
  credentials. Replace the example registry values, and keep real credentials
  out of manifests and source control. `multi-container-patterns.yaml` and
  `windows-pod-projected.yaml` likewise need their documented images and
  referenced ConfigMaps, Secrets, Services, or compatible node OS.
- `ssh.yaml` is a host-networked debug shell, not an SSH server. Replace its
  node name and use `kubectl exec -it node-debug-shell -- /bin/sh` on a trusted
  cluster.
- `host-volume.yaml` requires `/data` to exist on the selected node.
  `netns-volume.yaml` uses host networking, host namespaces, and a privileged
  container; only use it on a disposable, trusted node.
- `admin-service-account.yaml` grants effective cluster-admin privileges.
  Avoid creating this account in shared or production clusters.
- `evaluate-pod-creation.sh` creates and deletes a Pod and Service. Inspect it
  and use only in an isolated test cluster.

## Historical manifests

Files whose first comment begins `HISTORICAL:` document old, provider-specific
or release-specific setups; they are not current defaults. In particular,
`job-master.yaml` and `job-node.yaml` target kube-bench for Kubernetes v1.13
and mount node host paths, while `nodelocaldns-azure-cni.yaml` and
`nodelocaldns-kubenet.yaml` rely on older networking and kubelet configuration
assumptions. Do not apply them to a current cluster as generic v1.37.1
instructions.

## Image pins

The NGINX stable pin is `1.30.5`, released 2026-09-15 with the security fix
recorded as CVE-2026-90439 in the official
[1.30 changelog](https://nginx.org/en/CHANGES-1.30). The public image tags
below were checked on 2026-10-05. Tags are more reproducible than `latest`,
but are not digest locks; pin image digests as well when a deployment requires
immutable artifacts.

| Image family | Tag used | Upstream source |
| --- | --- | --- |
| NGINX | `1.30.5` | [Official NGINX image](https://hub.docker.com/_/nginx); [1.30 stable changelog](https://nginx.org/en/CHANGES-1.30) |
| Unprivileged NGINX | `1.30.5-alpine3.24` | [NGINX unprivileged image](https://hub.docker.com/r/nginxinc/nginx-unprivileged); [1.30 stable changelog](https://nginx.org/en/CHANGES-1.30) |
| Alpine | `3.24.2` | [Official Alpine image](https://hub.docker.com/_/alpine); [3.24.2 stable release (2026-09-17)](https://www.alpinelinux.org/posts/Alpine-3.21.8-3.22.6-3.23.6-3.24.2-released.html) |
| BusyBox | `1.37.0` | [BusyBox](https://busybox.net/) |
| Python | `3.14.8-slim-trixie` | [Official Python image](https://hub.docker.com/_/python); [3.14.8 release (2026-09-30)](https://www.python.org/downloads/release/python-3148/) |
| Redis | `8.10.2` | [Official Redis image](https://hub.docker.com/_/redis) |
| PostgreSQL | `18.6-alpine3.24` | [Official PostgreSQL image](https://hub.docker.com/_/postgres) |
| TensorFlow | `2.21.0` | [TensorFlow Docker images](https://hub.docker.com/r/tensorflow/tensorflow) |
| Fluent Bit | `5.1.3` | [Container image docs](https://docs.fluentbit.io/manual/installation/downloads/docker); [5.1.3 upstream release (2026-10-01)](https://github.com/fluent/fluent-bit/releases/tag/v5.1.3) |
| NodeLocal DNS cache | `1.26.8` | [Kubernetes DNS releases](https://github.com/kubernetes/dns/releases) |
| Ubuntu | `26.04` | [Official Ubuntu image](https://hub.docker.com/_/ubuntu) |
| Kubernetes echoserver | `1.10` | [Kubernetes echoserver source](https://github.com/kubernetes/kubernetes/tree/master/test/images/echoserver) |