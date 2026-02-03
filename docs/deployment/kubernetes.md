# Kubernetes

## Quick start

1. `kubectl apply -f k8s/namespace.yaml`
2. Edit `k8s/secret.yaml` and `kubectl apply -f k8s/secret.yaml`
3. `kubectl apply -f k8s/configmap.yaml`
4. `kubectl apply -f k8s/pvc.yaml`
5. `kubectl apply -f k8s/deployment.yaml` and `k8s/service.yaml`
6. Optional: `k8s/ingress.yaml`, `k8s/hpa.yaml`

See `k8s/README.md` for manifest details.
