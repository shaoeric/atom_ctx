# Server Deployment

AtomCtx can run as a standalone HTTP server, allowing multiple clients to connect over the network.

## Quick Start

```bash
# Start server (reads ~/.ctx/ctx.conf by default)
ctx-server

# Or specify a custom config path
ctx-server --config /path/to/ctx.conf

# Verify it's running
curl http://localhost:1933/health
# {"status": "ok"}
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config` | Path to ctx.conf file | `~/.ctx/ctx.conf` |
| `--host` | Host to bind to | `0.0.0.0` |
| `--port` | Port to bind to | `1933` |

**Examples**

```bash
# With default config
ctx-server

# With custom port
ctx-server --port 8000

# With custom config, host, and port
ctx-server --config /path/to/ctx.conf --host 127.0.0.1 --port 8000
```

## Configuration

The server reads all configuration from `ctx.conf`. See [Configuration Guide](./01-configuration.md) for full details on config file format.

The `server` section in `ctx.conf` controls server behavior:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 1933,
    "root_api_key": "your-secret-root-key",
    "cors_origins": ["*"]
  },
  "storage": {
    "workspace": "./data",
    "agfs": { "backend": "local" },
    "vectordb": { "backend": "local" }
  }
}
```

## Deployment Modes

### Standalone (Embedded Storage)

Server manages local AGFS and VectorDB. Configure the storage path in `ctx.conf`:

```json
{
  "storage": {
    "workspace": "./data",
    "agfs": { "backend": "local" },
    "vectordb": { "backend": "local" }
  }
}
```

```bash
ctx-server
```

### Hybrid (Remote Storage)

Server connects to remote AGFS and VectorDB services. Configure remote URLs in `ctx.conf`:

```json
{
  "storage": {
    "agfs": { "backend": "remote", "url": "http://agfs:1833" },
    "vectordb": { "backend": "remote", "url": "http://vectordb:8000" }
  }
}
```

```bash
ctx-server
```

## Deploying with Systemd (Recommended)

For Linux systems, you can use Systemd to manage AtomCtx as a service, enabling automatic restart and startup on boot. Firstly, you should tried to install and configure atom_ctx on your own.

### Create Systemd Service File

Create `/etc/systemd/system/atom_ctx.service` file:

```ini
[Unit]
Description=AtomCtx HTTP Server
After=network.target

[Service]
Type=simple
# Replace with your working directory
WorkingDirectory=/var/lib/atom_ctx
# Choose one of the following start methods
ExecStart=/usr/bin/ctx-server
Restart=always
RestartSec=5
# Path to config file
Environment="CTX_CONFIG_FILE=/etc/ctx/ctx.conf"

[Install]
WantedBy=multi-user.target
```

### Manage the Service

After creating the service file, use the following commands to manage the AtomCtx service:

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Start the service
sudo systemctl start atom_ctx.service

# Enable service on boot
sudo systemctl enable atom_ctx.service

# Check service status
sudo systemctl status atom_ctx.service

# View service logs
sudo journalctl -u atom_ctx.service -f
```

## Connecting Clients

### Python SDK

```python
import atom_ctx as ctx

client = ctx.SyncHTTPClient(url="http://localhost:1933", api_key="your-key", agent_id="my-agent")
client.initialize()

results = client.find("how to use atom_ctx")
client.close()
```

### CLI

The CLI reads connection settings from `ctx-cli.conf`. Create `~/.ctx/ctx-cli.conf`:

```json
{
  "url": "http://localhost:1933",
  "api_key": "your-key"
}
```

Or set the config path via environment variable:

```bash
export CTX_CLI_CONFIG_FILE=/path/to/ctx-cli.conf
```

Then use the CLI:

```bash
python -m atom_ctx ls ctx://resources/
```

### curl

```bash
curl http://localhost:1933/api/v1/fs/ls?uri=ctx:// \
  -H "X-API-Key: your-key"
```

## Cloud Deployment

### Docker

AtomCtx provides pre-built Docker images published to GitHub Container Registry:

```bash
docker run -d \
  --name atom_ctx \
  -p 1933:1933 \
  -v ~/.ctx/ctx.conf:/app/ctx.conf \
  -v /var/lib/atom_ctx/data:/app/data \
  --restart unless-stopped \
  ghcr.io/volcengine/atom_ctx:main
```

You can also use Docker Compose with the `docker-compose.yml` provided in the project root:

```bash
docker compose up -d
```

To build the image yourself: `docker build -t atom_ctx:latest .`

### Kubernetes + Helm

The project provides a Helm chart located at `examples/k8s-helm/`:

```bash
helm install atom_ctx ./examples/k8s-helm \
  --set atom_ctx.config.embedding.dense.api_key="YOUR_API_KEY" \
  --set atom_ctx.config.vlm.api_key="YOUR_API_KEY"
```

For a detailed cloud deployment guide (including Volcengine TOS + VikingDB + Ark configuration), see the [Cloud Deployment Guide](../../../examples/cloud/GUIDE.md).

## Health Checks

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /health` | No | Liveness probe — returns `{"status": "ok"}` immediately |
| `GET /ready` | No | Readiness probe — checks AGFS, VectorDB, APIKeyManager |

```bash
# Liveness
curl http://localhost:1933/health

# Readiness
curl http://localhost:1933/ready
# {"status": "ready", "checks": {"agfs": "ok", "vectordb": "ok", "api_key_manager": "ok"}}
```

Use `/health` for Kubernetes liveness probes and `/ready` for readiness probes.

## Related Documentation

- [Authentication](04-authentication.md) - API key setup
- [Monitoring](05-monitoring.md) - Health checks and observability
- [API Overview](../api/01-overview.md) - Complete API reference
