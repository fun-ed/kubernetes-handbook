#!/bin/bash
# Evaluate pod creation process.
# This is usually used for evaluating whether a cluster is configured properly.
set -e

create_pod() {
    # create a pod with memory limits.
    kubectl create -f- <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  containers:
  - name: dns-checker
    image: busybox:1.37.0
    command: ["sh", "-c", "sleep 3600"]
    resources:
      limits:
        memory: 128Mi
        cpu: 1000m
EOF
}

expose_pod() {
    pod=${POD:-"nginx"}
    kubectl expose pod "$pod" --port=80
}

evaluate_dns() {
    pod=${POD:-"nginx"}
    kubectl exec "$pod" -- nslookup kubernetes
    kubectl exec "$pod" -- nslookup kubernetes.default.svc.cluster.local
}

wait_for_status() {
  local times=10
  local wait=0.5
  local i

  for i in $(seq 1 $times); do
    res=$(kubectl get $1 $2 -o go-template="{{.status.phase}}")
    if [[ "$res" =~ ^$3$ ]]; then
      echo -n ${green}
      echo "Resource status of $1 $2 changed to $3"
      echo -n ${reset}
      return 0
    else
      echo "Current status of resource $1 $2 is $res"
    fi
    sleep ${wait}
  done

  echo -n ${red}
  echo "Timeout waiting resource $1 $2 status"
  echo -n ${reset}
  return 1
}

wait_for_non_exist() {
  local times=5
  local wait=0.5
  local i

  for i in $(seq 1 $times); do
    res=$(! kubectl get $1 $2 -o go-template="{{.metadata.name}} 2>/dev/null")
    if ! [[ "$res" =~ ^$2$ ]]; then
      echo -n ${green}
      echo "Resource $1 $2 deleted"
      echo -n ${reset}
      return 0
    fi
    sleep ${wait}
  done

  echo -n ${red}
  echo "Timeout for waiting resource $1 $2 non-exist"
  echo -n ${reset}
  return 1
}

create_pod
wait_for_status "--namespace=default pods" 'nginx' 'Running'
expose_pod
evaluate_dns
kubectl delete pod nginx
kubectl delete service nginx
wait_for_non_exist "--namespace=default pods" 'nginx'
