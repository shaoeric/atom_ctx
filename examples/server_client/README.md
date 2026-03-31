# AtomCtx Server-Client 示例

演示 AtomCtx 的 Server/Client 架构：通过 HTTP Server 提供服务，Client 通过 HTTP API 访问。

## 架构

```
┌──────────────┐     HTTP/REST     ┌──────────────────┐
│   Client     │ ◄──────────────► │  AtomCtx Server │
│  (HTTP mode) │   JSON API        │  (FastAPI + ASGI) │
└──────────────┘                   └──────────────────┘
```

## Quick Start

```bash
# 0. 安装依赖
uv sync

# 1. 配置 Server（ctx.conf）
#    Server 读取配置的优先级：
#      $CTX_CONFIG_FILE > ~/.ctx/ctx.conf
#    参见 ctx.conf.example 了解完整配置项

# 2. 启动 Server（另开终端）
ctx-server                            # 从默认路径读取 ctx.conf
ctx-server --config ./ctx.conf         # 指定配置文件
ctx-server --host 0.0.0.0 --port 1933 # 覆盖 host/port

# 3. 配置 CLI 连接（ctx-cli.conf）
#    CLI 读取配置的优先级：
#      $CTX_CLI_CONFIG_FILE > ~/.ctx/ctx-cli.conf
#    示例内容：
#      {"url": "http://localhost:1933", "api_key": null, "output": "table"}

# 4. 运行 Client 示例
uv run client_sync.py                    # 同步客户端
uv run client_async.py                   # 异步客户端
bash client_cli.sh                       # CLI 使用示例
```

## 文件说明

```
client_sync.py      # 同步客户端示例（SyncHTTPClient）
client_async.py     # 异步客户端示例（AsyncHTTPClient）
client_cli.sh       # CLI 使用示例（覆盖所有命令和参数）
ctx.conf.example     # Server/SDK 配置文件模板（ctx.conf）
ctx-cli.conf.example  # CLI 连接配置文件模板（ctx-cli.conf）
pyproject.toml      # 项目依赖
```

## 配置文件

新的配置系统使用两个配置文件，不再支持单字段环境变量（如 ATOM_CTX_URL、ATOM_CTX_API_KEY、ATOM_CTX_HOST、ATOM_CTX_PORT、ATOM_CTX_PATH、ATOM_CTX_VECTORDB_URL、ATOM_CTX_AGFS_URL 均已移除）。

仅保留 2 个环境变量：

| 环境变量 | 说明 | 默认路径 |
|---------|------|---------|
| `CTX_CONFIG_FILE` | ctx.conf 配置文件路径 | `~/.ctx/ctx.conf` |
| `CTX_CLI_CONFIG_FILE` | ctx-cli.conf 配置文件路径 | `~/.ctx/ctx-cli.conf` |

### ctx.conf（SDK 嵌入 + Server）

用于 SDK 嵌入模式和 Server 启动，包含 `server` 段配置。参见 `ctx.conf.example`。

### ctx-cli.conf（CLI 连接配置）

用于 CLI 连接远程 Server：

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `url` | Server 地址 | （必填） |
| `api_key` | API Key 认证 | `null`（无认证） |
| `output` | 默认输出格式：`"table"` 或 `"json"` | `"table"` |

```json
{
  "url": "http://localhost:1933",
  "api_key": null,
  "output": "table"
}
```

## Server 启动方式

### CLI 命令

```bash
# 基本启动（从 ~/.ctx/ctx.conf 或 $CTX_CONFIG_FILE 读取配置）
ctx-server

# 指定配置文件
ctx-server --config ./ctx.conf

# 覆盖 host/port
ctx-server --host 0.0.0.0 --port 1933
```

`ctx-server` 命令支持 `--config`、`--host`、`--port` 三个选项。认证密钥等其他配置通过 ctx.conf 的 `server` 段设置。

### Python 脚本

```python
from atom_ctx.server.bootstrap import main
main()
```

## Client 使用方式

### 同步客户端

```python
import atom_ctx as ctx

client = ctx.SyncHTTPClient(url="http://localhost:1933", api_key="your-key", timeout=120.0)
client.initialize()

client.add_resource(path="./document.md")
client.wait_processed()

results = client.find("search query")
client.close()
```

### 异步客户端

```python
import atom_ctx as ctx

client = ctx.AsyncHTTPClient(url="http://localhost:1933", api_key="your-key", timeout=120.0)
await client.initialize()

await client.add_resource(path="./document.md")
await client.wait_processed()

results = await client.find("search query")
await client.close()
```

### CLI

```bash
# CLI 从 ~/.ctx/ctx-cli.conf 或 $s 读取连接配置

# 基本操作
atom_ctx health
atom_ctx add-resource ./document.md   # 上传文件
atom_ctx add-resource ./dir --exclude "*.tmp,*.log" --ignore-dirs "subdir-a,subdir-b/subsubdir-c" # 上传文件夹

atom_ctx wait
atom_ctx find "search query"

# 输出格式（全局选项，须放在子命令之前）
atom_ctx -o table find "query"         # 表格输出（默认）
atom_ctx -o json find "query"          # 紧凑 JSON + {"ok":true} 包装（脚本用）

# Session 操作
atom_ctx session new
atom_ctx session add-message <session-id> --role user --content "hello"
atom_ctx session commit <session-id>
atom_ctx session delete <session-id>
```

完整 CLI 使用示例参见 `client_cli.sh`。

## API 端点一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查（免认证） |
| GET | `/api/v1/system/status` | 系统状态 |
| POST | `/api/v1/resources` | 添加资源 |
| POST | `/api/v1/resources/skills` | 添加技能 |
| POST | `/api/v1/resources/wait` | 等待处理完成 |
| GET | `/api/v1/fs/ls` | 列出目录 |
| GET | `/api/v1/fs/tree` | 目录树 |
| GET | `/api/v1/fs/stat` | 资源状态 |
| POST | `/api/v1/fs/mkdir` | 创建目录 |
| DELETE | `/api/v1/fs/rm` | 删除资源 |
| POST | `/api/v1/fs/mv` | 移动资源 |
| GET | `/api/v1/content/read` | 读取内容 |
| GET | `/api/v1/content/abstract` | 获取摘要 |
| GET | `/api/v1/content/overview` | 获取概览 |
| POST | `/api/v1/search/find` | 语义搜索 |
| POST | `/api/v1/search/search` | 带 Session 搜索 |
| POST | `/api/v1/search/grep` | 内容搜索 |
| POST | `/api/v1/search/glob` | 文件匹配 |
| GET | `/api/v1/relations` | 获取关联 |
| POST | `/api/v1/relations/link` | 创建关联 |
| DELETE | `/api/v1/relations/unlink` | 删除关联 |
| POST | `/api/v1/sessions` | 创建 Session |
| GET | `/api/v1/sessions` | 列出 Sessions |
| GET | `/api/v1/sessions/{id}` | 获取 Session |
| DELETE | `/api/v1/sessions/{id}` | 删除 Session |
| POST | `/api/v1/sessions/{id}/messages` | 添加消息 |
| POST | `/api/v1/sessions/{id}/commit` | 提交 Session（归档消息、提取记忆） |
| POST | `/api/v1/pack/export` | 导出 ctxpack |
| POST | `/api/v1/pack/import` | 导入 ctxpack |
| GET | `/api/v1/observer/system` | 系统监控 |
| GET | `/api/v1/observer/queue` | 队列状态 |
| GET | `/api/v1/observer/vikingdb` | VikingDB 状态 |
| GET | `/api/v1/observer/vlm` | VLM 状态 |
| GET | `/api/v1/debug/health` | 组件健康检查 |

## 认证

Server 支持可选的 API Key 认证。通过 ctx.conf 的 `server.api_key` 字段设置。

Client 请求时通过以下任一方式传递：

```
X-API-Key: your-secret-key
Authorization: Bearer your-secret-key
```

CLI 的 API Key 通过 ctx-cli.conf 的 `api_key` 字段配置。

`/health` 端点始终免认证。
