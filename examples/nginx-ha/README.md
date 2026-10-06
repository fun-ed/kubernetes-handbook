# Zero Downtime Service Updates

The manifests accompany the linked article's discussion of rolling updates and
node drains. Apply only this sample directory from the repository root.

The manifests demonstrate one replica set behind a Service and a disruption
budget. They are not a production high-availability recipe: review the
application's readiness behavior, graceful shutdown, topology, load-balancer
health checks, storage, and cluster-specific eviction limits first. A
PodDisruptionBudget does not prevent all outages or guarantee that a drain
completes.

## Deploy the sample

From the repository root:

```sh
kubectl apply -f examples/nginx-ha/
```

## Observe service during node drain

Replace the node and address with values from your own test cluster. Draining
evicts eligible Pods and can disrupt workloads; use an isolated cluster and
confirm the PodDisruptionBudget allows the operation.

```sh
kubectl get pods -l app=nginx -o wide
echo "GET http://${LOAD_BALANCER_IP}" | vegeta attack -rate=100 -timeout=10s -duration=1m | vegeta report
kubectl drain "${NODE}" --ignore-daemonsets --delete-emptydir-data
```

Install Vegeta from its [official instructions](https://github.com/tsenart/vegeta#install)
and use an address reachable from the client. The load-test rate and duration
are examples, not capacity guidance. A node drain can still interrupt existing
connections; validate the actual load-balancer health-check behavior.

## Cleanup

```sh
kubectl uncordon "${NODE}"
kubectl delete -f examples/nginx-ha/
```
