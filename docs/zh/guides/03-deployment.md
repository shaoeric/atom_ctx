# 服务端部署

AtomCtx 可以作为独立的 HTTP 服务器运行，允许多个客户端通过网络连接。

## 快速开始

```bash
# 配置文件在默认路径 ~/.ctx/ctx.conf 时，直接启动
ctx-server

# 配置文件在其他位置时，通过 --config 指定
ctx-server --config /path/to/ctx.conf

# 验证服务器是否运行
curl http://localhost:1933/health
# {"status": "ok"}
```

## 命令行选项

| 选项 | 描述 | 默认值 |
|------|------|--------|
| `--config` | 配置文件路径 | `~/.ctx/ctx.conf` |
| `--host` | 绑定的主机地址 | `0.0.0.0` |
| `--port` | 绑定的端口 | `1933` |

**示例**

```bash
# 使用默认配置
ctx-server

# 使用自定义端口
ctx-server --port 8000

# 指定配置文件、主机地址和端口
ctx-server --config /path/to/ctx.conf --host 127.0.0.1 --port 8000
```

## 配置

服务端从 `ctx.conf` 读取所有配置。配置文件各段详情见 [配置指南](01-configuration.md)。

`ctx.conf` 中的 `server` 段控制服务端行为：

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

## 部署模式

### 独立模式（嵌入存储）

服务器管理本地 AGFS 和 VectorDB。在 `ctx.conf` 中配置本地存储路径：

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

### 混合模式（远程存储）

服务器连接到远程 AGFS 和 VectorDB 服务。在 `ctx.conf` 中配置远程地址：

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

## 使用 Systemd 部署服务（推荐）

对于 Linux 系统，可以使用 Systemd 服务来管理 AtomCtx，实现自动重启、开机自启等功能。首先，你应该已经成功安装并配置了 AtomCtx 服务器，确保它可以正常运行，再进行服务化部署。

### 创建 Systemd 服务文件

创建 `/etc/systemd/system/atom_ctx.service` 文件：

```ini
[Unit]
Description=AtomCtx HTTP Server
After=network.target

[Service]
Type=simple
# 替换为运行 AtomCtx 的用户
User=your-username
# 替换为用户组
Group=your-group
# 替换为工作目录
WorkingDirectory=/var/lib/atom_ctx
# 以下两种启动方式二选一
ExecStart=/path/to/your/python/bin/ctx-server
Restart=always
RestartSec=5
# 配置文件路径
Environment="CTX_CONFIG_FILE=/etc/ctx/ctx.conf"

[Install]
WantedBy=multi-user.target
```

### 管理服务

创建好服务文件后，使用以下命令管理 AtomCtx 服务：

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start atom_ctx.service

# 设置开机自启
sudo systemctl enable atom_ctx.service

# 查看服务状态
sudo systemctl status atom_ctx.service

# 查看服务日志
sudo journalctl -u atom_ctx.service -f
```

## 连接客户端

### Python SDK

```python
import atom_ctx as ctx

client = ctx.SyncHTTPClient(url="http://localhost:1933", api_key="your-key", agent_id="my-agent")
client.initialize()

results = client.find("how to use atom_ctx")
client.close()
```

### CLI

CLI 从 `ctx-cli.conf` 读取连接配置。在 `~/.ctx/ctx-cli.conf` 中配置：

```json
{
  "url": "http://localhost:1933",
  "api_key": "your-key"
}
```

也可通过 `CTX_CLI_CONFIG_FILE` 环境变量指定配置文件路径：

```bash
export CTX_CLI_CONFIG_FILE=/path/to/ctx-cli.conf
```

### curl

```bash
curl http://localhost:1933/api/v1/fs/ls?uri=ctx:// \
  -H "X-API-Key: your-key"
```

## 云上部署

### Docker

AtomCtx 提供预构建的 Docker 镜像，发布在 GitHub Container Registry：

```bash
docker run -d \
  --name atom_ctx \
  -p 1933:1933 \
  -v ~/.ctx/ctx.conf:/app/ctx.conf \
  -v /var/lib/atom_ctx/data:/app/data \
  --restart unless-stopped \
  ghcr.io/volcengine/atom_ctx:main
```

也可以使用 Docker Compose，项目根目录提供了 `docker-compose.yml`：

```bash
docker compose up -d
```

如需自行构建镜像：`docker build -t atom_ctx:latest .`

### Kubernetes + Helm

项目提供了 Helm chart，位于 `examples/k8s-helm/`：

```bash
helm install atom_ctx ./examples/k8s-helm \
  --set atom_ctx.config.embedding.dense.api_key="YOUR_API_KEY" \
  --set atom_ctx.config.vlm.api_key="YOUR_API_KEY"
```

详细的云上部署指南（包括火山引擎 TOS + VikingDB + 方舟配置）请参考 [云上部署指南](../../../examples/cloud/GUIDE.md)。

## 健康检查

| 端点 | 认证 | 用途 |
|------|------|------|
| `GET /health` | 否 | 存活探针 — 立即返回 `{"status": "ok"}` |
| `GET /ready` | 否 | 就绪探针 — 检查 AGFS、VectorDB、APIKeyManager |

```bash
# 存活探针
curl http://localhost:1933/health

# 就绪探针
curl http://localhost:1933/ready
# {"status": "ready", "checks": {"agfs": "ok", "vectordb": "ok", "api_key_manager": "ok"}}
```

在 Kubernetes 中，使用 `/health` 作为存活探针，`/ready` 作为就绪探针。

## 相关文档

- [认证](04-authentication.md) - API Key 设置
- [监控](05-monitoring.md) - 健康检查与可观测性
- [API 概览](../api/01-overview.md) - 完整 API 参考
