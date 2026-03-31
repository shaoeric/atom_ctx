# 文件系统

AtomCtx 提供类 Unix 的文件系统操作来管理上下文。

## API 参考

### abstract()

读取 L0 摘要（约 100 token 的概要）。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | Ctx URI（必须是目录） |

**Python SDK (Embedded / HTTP)**

```python
abstract = client.abstract("ctx://resources/docs/")
print(f"Abstract: {abstract}")
# Output: "Documentation for the project API, covering authentication, endpoints..."
```

**HTTP API**

```
GET /api/v1/content/abstract?uri={uri}
```

```bash
curl -X GET "http://localhost:1933/api/v1/content/abstract?uri=ctx://resources/docs/" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
atom_ctx abstract ctx://resources/docs/
```

**响应**

```json
{
  "status": "ok",
  "result": "Documentation for the project API, covering authentication, endpoints...",
  "time": 0.1
}
```

---

### overview()

读取 L1 概览，适用于目录。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | Ctx URI（必须是目录） |

**Python SDK (Embedded / HTTP)**

```python
overview = client.overview("ctx://resources/docs/")
print(f"Overview:\n{overview}")
```

**HTTP API**

```
GET /api/v1/content/overview?uri={uri}
```

```bash
curl -X GET "http://localhost:1933/api/v1/content/overview?uri=ctx://resources/docs/" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
atom_ctx overview ctx://resources/docs/
```

**响应**

```json
{
  "status": "ok",
  "result": "## docs/\n\nContains API documentation and guides...",
  "time": 0.1
}
```

---

### read()

读取 L2 完整内容。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | Ctx URI |

**Python SDK (Embedded / HTTP)**

```python
content = client.read("ctx://resources/docs/api.md")
print(f"Content:\n{content}")
```

**HTTP API**

```
GET /api/v1/content/read?uri={uri}
```

```bash
curl -X GET "http://localhost:1933/api/v1/content/read?uri=ctx://resources/docs/api.md" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
atom_ctx read ctx://resources/docs/api.md
```

**响应**

```json
{
  "status": "ok",
  "result": "# API Documentation\n\nFull content of the file...",
  "time": 0.1
}
```

---

### ls()

列出目录内容。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | Ctx URI |
| simple | bool | 否 | False | 仅返回相对路径 |
| recursive | bool | 否 | False | 递归列出所有子目录 |

**条目结构**

```python
{
    "name": "docs",           # 文件/目录名称
    "size": 4096,             # 大小（字节）
    "mode": 16877,            # 文件模式
    "modTime": "2024-01-01T00:00:00Z",  # ISO 时间戳
    "isDir": True,            # 如果是目录则为 True
    "uri": "ctx://resources/docs/",  # Ctx URI
    "meta": {}                # 可选元数据
}
```

**Python SDK (Embedded / HTTP)**

```python
entries = client.ls("ctx://resources/")
for entry in entries:
    type_str = "dir" if entry['isDir'] else "file"
    print(f"{entry['name']} - {type_str}")
```

**HTTP API**

```
GET /api/v1/fs/ls?uri={uri}&simple={bool}&recursive={bool}
```

```bash
# 基本列表
curl -X GET "http://localhost:1933/api/v1/fs/ls?uri=ctx://resources/" \
  -H "X-API-Key: your-key"

# 简单路径列表
curl -X GET "http://localhost:1933/api/v1/fs/ls?uri=ctx://resources/&simple=true" \
  -H "X-API-Key: your-key"

# 递归列表
curl -X GET "http://localhost:1933/api/v1/fs/ls?uri=ctx://resources/&recursive=true" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
atom_ctx ls ctx://resources/ [--simple] [--recursive]
```

**响应**

```json
{
  "status": "ok",
  "result": [
    {
      "name": "docs",
      "size": 4096,
      "mode": 16877,
      "modTime": "2024-01-01T00:00:00Z",
      "isDir": true,
      "uri": "ctx://resources/docs/"
    }
  ],
  "time": 0.1
}
```

---

### tree()

获取目录树结构。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | Ctx URI |

**Python SDK (Embedded / HTTP)**

```python
entries = client.tree("ctx://resources/")
for entry in entries:
    type_str = "dir" if entry['isDir'] else "file"
    print(f"{entry['rel_path']} - {type_str}")
```

**HTTP API**

```
GET /api/v1/fs/tree?uri={uri}
```

```bash
curl -X GET "http://localhost:1933/api/v1/fs/tree?uri=ctx://resources/" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
atom_ctx tree ctx://resources/my-project/
```

**响应**

```json
{
  "status": "ok",
  "result": [
    {
      "name": "docs",
      "size": 4096,
      "isDir": true,
      "rel_path": "docs/",
      "uri": "ctx://resources/docs/"
    },
    {
      "name": "api.md",
      "size": 1024,
      "isDir": false,
      "rel_path": "docs/api.md",
      "uri": "ctx://resources/docs/api.md"
    }
  ],
  "time": 0.1
}
```

---

### stat()

获取文件或目录的状态信息。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | Ctx URI |

**Python SDK (Embedded / HTTP)**

```python
info = client.stat("ctx://resources/docs/api.md")
print(f"Size: {info['size']}")
print(f"Is directory: {info['isDir']}")
```

**HTTP API**

```
GET /api/v1/fs/stat?uri={uri}
```

```bash
curl -X GET "http://localhost:1933/api/v1/fs/stat?uri=ctx://resources/docs/api.md" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
atom_ctx stat ctx://resources/my-project/docs/api.md
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "name": "api.md",
    "size": 1024,
    "mode": 33188,
    "modTime": "2024-01-01T00:00:00Z",
    "isDir": false,
    "uri": "ctx://resources/docs/api.md"
  },
  "time": 0.1
}
```

---

### mkdir()

创建目录。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | 新目录的 Ctx URI |

**Python SDK (Embedded / HTTP)**

```python
client.mkdir("ctx://resources/new-project/")
```

**HTTP API**

```
POST /api/v1/fs/mkdir
```

```bash
curl -X POST http://localhost:1933/api/v1/fs/mkdir \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "uri": "ctx://resources/new-project/"
  }'
```

**CLI**

```bash
atom_ctx mkdir ctx://resources/new-project/
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "uri": "ctx://resources/new-project/"
  },
  "time": 0.1
}
```

---

### rm()

删除文件或目录。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | 要删除的 Ctx URI |
| recursive | bool | 否 | False | 递归删除目录 |

**Python SDK (Embedded / HTTP)**

```python
# 删除单个文件
client.rm("ctx://resources/docs/old.md")

# 递归删除目录
client.rm("ctx://resources/old-project/", recursive=True)
```

**HTTP API**

```
DELETE /api/v1/fs?uri={uri}&recursive={bool}
```

```bash
# 删除单个文件
curl -X DELETE "http://localhost:1933/api/v1/fs?uri=ctx://resources/docs/old.md" \
  -H "X-API-Key: your-key"

# 递归删除目录
curl -X DELETE "http://localhost:1933/api/v1/fs?uri=ctx://resources/old-project/&recursive=true" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
atom_ctx rm ctx://resources/old.md [--recursive]
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "uri": "ctx://resources/docs/old.md"
  },
  "time": 0.1
}
```

---

### mv()

移动文件或目录。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| from_uri | str | 是 | - | 源 Ctx URI |
| to_uri | str | 是 | - | 目标 Ctx URI |

**Python SDK (Embedded / HTTP)**

```python
client.mv(
    "ctx://resources/old-name/",
    "ctx://resources/new-name/"
)
```

**HTTP API**

```
POST /api/v1/fs/mv
```

```bash
curl -X POST http://localhost:1933/api/v1/fs/mv \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "from_uri": "ctx://resources/old-name/",
    "to_uri": "ctx://resources/new-name/"
  }'
```

**CLI**

```bash
atom_ctx mv ctx://resources/old-name/ ctx://resources/new-name/
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "from": "ctx://resources/old-name/",
    "to": "ctx://resources/new-name/"
  },
  "time": 0.1
}
```

---

### grep()

按模式搜索内容。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | 要搜索的 Ctx URI |
| pattern | str | 是 | - | 搜索模式（正则表达式） |
| case_insensitive | bool | 否 | False | 忽略大小写 |

**Python SDK (Embedded / HTTP)**

```python
results = client.grep(
    "ctx://resources/",
    "authentication",
    case_insensitive=True
)

print(f"Found {results['count']} matches")
for match in results['matches']:
    print(f"  {match['uri']}:{match['line']}")
    print(f"    {match['content']}")
```

**HTTP API**

```
POST /api/v1/search/grep
```

```bash
curl -X POST http://localhost:1933/api/v1/search/grep \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "uri": "ctx://resources/",
    "pattern": "authentication",
    "case_insensitive": true
  }'
```

**CLI**

```bash
atom_ctx grep ctx://resources/ "authentication" [--ignore-case]
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "matches": [
      {
        "uri": "ctx://resources/docs/auth.md",
        "line": 15,
        "content": "User authentication is handled by..."
      }
    ],
    "count": 1
  },
  "time": 0.1
}
```

---

### glob()

按模式匹配文件。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| pattern | str | 是 | - | Glob 模式（例如 `**/*.md`） |
| uri | str | 否 | "ctx://" | 起始 URI |

**Python SDK (Embedded / HTTP)**

```python
# 查找所有 Markdown 文件
results = client.glob("**/*.md", "ctx://resources/")
print(f"Found {results['count']} markdown files:")
for uri in results['matches']:
    print(f"  {uri}")

# 查找所有 Python 文件
results = client.glob("**/*.py", "ctx://resources/")
print(f"Found {results['count']} Python files")
```

**HTTP API**

```
POST /api/v1/search/glob
```

```bash
curl -X POST http://localhost:1933/api/v1/search/glob \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "pattern": "**/*.md",
    "uri": "ctx://resources/"
  }'
```

**CLI**

```bash
atom_ctx glob "**/*.md" [--uri ctx://resources/]
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "matches": [
      "ctx://resources/docs/api.md",
      "ctx://resources/docs/guide.md"
    ],
    "count": 2
  },
  "time": 0.1
}
```

---

### link()

创建资源之间的关联。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| from_uri | str | 是 | - | 源 URI |
| uris | str 或 List[str] | 是 | - | 目标 URI |
| reason | str | 否 | "" | 关联原因 |

**Python SDK (Embedded / HTTP)**

```python
# 单个关联
client.link(
    "ctx://resources/docs/auth/",
    "ctx://resources/docs/security/",
    reason="Security best practices for authentication"
)

# 多个关联
client.link(
    "ctx://resources/docs/api/",
    [
        "ctx://resources/docs/auth/",
        "ctx://resources/docs/errors/"
    ],
    reason="Related documentation"
)
```

**HTTP API**

```
POST /api/v1/relations/link
```

```bash
# 单个关联
curl -X POST http://localhost:1933/api/v1/relations/link \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "from_uri": "ctx://resources/docs/auth/",
    "to_uris": "ctx://resources/docs/security/",
    "reason": "Security best practices for authentication"
  }'

# 多个关联
curl -X POST http://localhost:1933/api/v1/relations/link \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "from_uri": "ctx://resources/docs/api/",
    "to_uris": ["ctx://resources/docs/auth/", "ctx://resources/docs/errors/"],
    "reason": "Related documentation"
  }'
```

**CLI**

```bash
atom_ctx link ctx://resources/docs/auth/ ctx://resources/docs/security/ --reason "Security best practices"
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "from": "ctx://resources/docs/auth/",
    "to": "ctx://resources/docs/security/"
  },
  "time": 0.1
}
```

---

### relations()

获取资源的关联关系。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| uri | str | 是 | - | Ctx URI |

**Python SDK (Embedded / HTTP)**

```python
relations = client.relations("ctx://resources/docs/auth/")
for rel in relations:
    print(f"Related: {rel['uri']}")
    print(f"  Reason: {rel['reason']}")
```

**HTTP API**

```
GET /api/v1/relations?uri={uri}
```

```bash
curl -X GET "http://localhost:1933/api/v1/relations?uri=ctx://resources/docs/auth/" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
atom_ctx relations ctx://resources/docs/auth/
```

**响应**

```json
{
  "status": "ok",
  "result": [
    {"uri": "ctx://resources/docs/security/", "reason": "Security best practices"},
    {"uri": "ctx://resources/docs/errors/", "reason": "Error handling"}
  ],
  "time": 0.1
}
```

---

### unlink()

移除关联关系。

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| from_uri | str | 是 | - | 源 URI |
| uri | str | 是 | - | 要取消关联的目标 URI |

**Python SDK (Embedded / HTTP)**

```python
client.unlink(
    "ctx://resources/docs/auth/",
    "ctx://resources/docs/security/"
)
```

**HTTP API**

```
DELETE /api/v1/relations/link
```

```bash
curl -X DELETE http://localhost:1933/api/v1/relations/link \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "from_uri": "ctx://resources/docs/auth/",
    "to_uri": "ctx://resources/docs/security/"
  }'
```

**CLI**

```bash
atom_ctx unlink ctx://resources/docs/auth/ ctx://resources/docs/security/
```

**响应**

```json
{
  "status": "ok",
  "result": {
    "from": "ctx://resources/docs/auth/",
    "to": "ctx://resources/docs/security/"
  },
  "time": 0.1
}
```

---

## 相关文档

- [Ctx URI](../concepts/04-ctx-uri.md) - URI 规范
- [Context Layers](../concepts/03-context-layers.md) - L0/L1/L2
- [Resources](02-resources.md) - 资源管理
