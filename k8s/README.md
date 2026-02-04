# Kubernetes manifests

Namespace, configmap, secret, deployment, service, ingress, HPA, PVC. Edit `secret.yaml` and optionally `ingress.yaml` (host). Apply in order: namespace → secret → configmap → pvc → deployment, service → ingress, hpa. See [docs/deployment/kubernetes.md](../docs/deployment/kubernetes.md).
