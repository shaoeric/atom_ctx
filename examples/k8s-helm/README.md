# AtomCtx Helm Chart

This Helm chart deploys AtomCtx on Kubernetes, providing a scalable and production-ready RAG (Retrieval-Augmented Generation) and semantic search service.

## Overview

[AtomCtx](https://github.com/volcengine/atom-ctx) is an open-source RAG and semantic search engine that serves as a Context Database MCP (Model Context Protocol) server. This Helm chart enables easy deployment on Kubernetes clusters with support for major cloud providers.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- A valid Volcengine API key for embedding and VLM services

## Installation

### Add the Helm repository (when published)

```bash
helm repo add atom_ctx https://volcengine.github.io/atom_ctx
helm repo update
```

### Install from local chart

```bash
# Clone the repository
git clone https://github.com/volcengine/atom-ctx.git
cd AtomCtx/deploy/helm

# Install with default values
helm install atom_ctx ./atom_ctx

# Install with custom values
helm install atom_ctx ./atom_ctx -f my-values.yaml
```

### Quick Start

```bash
# GCP deployment
helm install atom_ctx ./atom_ctx \
  --set cloudProvider=gcp \
  --set atom_ctx.config.embedding.dense.api_key=YOUR_API_KEY

# AWS deployment
helm install atom_ctx ./atom_ctx \
  --set cloudProvider=aws \
  --set atom_ctx.config.embedding.dense.api_key=YOUR_API_KEY
```

## Configuration

### Cloud Provider Support

The chart supports automatic LoadBalancer annotation configuration for major cloud providers:

| Provider | Configuration Value |
|----------|-------------------|
| Google Cloud Platform | `cloudProvider: gcp` |
| Amazon Web Services | `cloudProvider: aws` |
| Other/Generic | `cloudProvider: ""` (default) |

### Key Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `cloudProvider` | Cloud provider for LoadBalancer annotations | `""` |
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Container image repository | `ghcr.io/astral-sh/uv` |
| `image.tag` | Container image tag | `python3.12-bookworm` |
| `service.type` | Kubernetes service type | `LoadBalancer` |
| `service.port` | Service port | `1933` |
| `atom_ctx.config.server.api_key` | API key for authentication | `null` |
| `atom_ctx.config.embedding.dense.api_key` | Volcengine API key | `null` |

### AtomCtx Configuration

All AtomCtx configuration options from `ctx.conf` are available under `atom_ctx.config`. See `values.yaml` for the complete default configuration.

### Embedding Configuration

The embedding service requires a Volcengine API key:

```yaml
atom_ctx:
  config:
    embedding:
      dense:
        api_key: "your-api-key-here"
        api_base: "https://ark.cn-beijing.volces.com/api/v3"
        model: "doubao-embedding-vision-250615"
```

### VLM Configuration

For vision-language model support:

```yaml
atom_ctx:
  config:
    vlm:
      api_key: "your-api-key-here"
      api_base: "https://ark.cn-beijing.volces.com/api/v3"
      model: "doubao-seed-2-0-pro-260215"
```

## Storage

### Default (emptyDir)

By default, the chart uses `emptyDir` volumes for data storage. This is suitable for development and testing but **data will be lost** when pods are restarted.

### Persistent Storage (Optional)

To enable persistent storage with PVC:

```yaml
atom_ctx:
  dataVolume:
    enabled: true
    usePVC: true
    size: 50Gi
    storageClassName: standard
    accessModes:
      - ReadWriteOnce
```

## Security

### API Key Authentication

Enable API key authentication to secure your AtomCtx server:

```yaml
atom_ctx:
  config:
    server:
      api_key: "your-secure-api-key"
      cors_origins:
        - "https://your-domain.com"
```

### Secrets Management

For production deployments, use Kubernetes secrets or external secret management:

```bash
# Create secret from literal
kubectl create secret generic atom_ctx-config \
  --from-literal=ctx.conf='{"server":{"api_key":"secret"}}'

# Or mount existing secret
helm install atom_ctx ./atom_ctx \
  --set existingSecret=atom_ctx-config
```

## Autoscaling

Enable Horizontal Pod Autoscaler for production workloads:

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80
```

## Resource Limits

Default resource configuration:

```yaml
resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 500m
    memory: 1Gi
```

Adjust based on your workload requirements.

## Usage Examples

### Connect with CLI

```bash
# Get the LoadBalancer IP
export ATOM_CTX_IP=$(kubectl get svc atom_ctx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Create CLI configuration
cat > ~/.ctx/ctx-cli.conf <<EOF
{
  "url": "http://$ATOM_CTX_IP:1933",
  "api_key": null,
  "output": "table"
}
EOF

# Test connection
atom_ctx health
```

### Python Client

```python
import atom_ctx as ctx

# Get service endpoint
# kubectl get svc atom_ctx

client = ctx.AtomCtx(url="http://<load-balancer-ip>:1933", api_key="your-key")
client.initialize()

# Add a resource
client.add_resource(path="./document.pdf")
client.wait_processed()

# Search
results = client.find("your search query")
print(results)

client.close()
```

## Troubleshooting

### Pod fails to start

Check the pod logs:
```bash
kubectl logs -l app.kubernetes.io/name=atom_ctx
```

### Health check fails

Verify the configuration:
```bash
kubectl get secret atom_ctx-config -o jsonpath='{.data.ov\.conf}' | base64 -d
```

### LoadBalancer not getting IP

Wait for the cloud provider to provision the load balancer:
```bash
kubectl get svc atom_ctx -w
```

Check cloud provider-specific annotations in `values.yaml`.

## Uninstallation

```bash
helm uninstall atom_ctx
```

To remove persistent data (if PVC was enabled):
```bash
kubectl delete pvc atom_ctx-data
```

## Contributing

Contributions are welcome! Please see the [AtomCtx repository](https://github.com/volcengine/atom-ctx) for contribution guidelines.

## License

This Helm chart is licensed under the Apache License 2.0, matching the AtomCtx project license.
