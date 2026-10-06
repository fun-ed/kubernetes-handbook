# Query Calico GlobalNetworkPolicy logs

Since Calico NetworkPolicy is based on iptables, calico-node logs only show its container's output, but not GlobalNetworkPolicy Log action. This example shows how to query those logs.

## Deploy

From the repository root, apply this Calico-specific sample only after meeting
the prerequisites in [`../README.md`](../README.md):

```sh
kubectl apply -f examples/calico/calico-packet-logs.yaml
```

## Read the collected logs

```sh
kubectl logs -n default -l app=calico-packet-logs --all-containers=true --prefix
```

