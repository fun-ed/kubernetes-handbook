# Network Policy examples

## Pre-requirements

Network policies are implemented by the network plugin, so you must be using a networking solution which supports NetworkPolicy - simply creating the resource without a controller to implement it will have no effect.

## Example workflow

From the repository root, apply only this directory:

```sh
kubectl apply -f examples/network-policy/
```

The access test should succeed; the no-access test retries for up to about
three minutes and then fails its connection. Use the observations only on a
CNI that enforces NetworkPolicy:

```sh
kubectl get pods -l app=access-pod
kubectl get pods -l app=no-access-pod
```
