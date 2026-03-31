# File System

AtomCtx provides Unix-like file system operations for managing context.

## API Reference

### abstract()

Read L0 abstract (~100 tokens summary).

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI (must be a directory) |

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

**Response**

```json
{
  "status": "ok",
  "result": "Documentation for the project API, covering authentication, endpoints...",
  "time": 0.1
}
```

---

### overview()

Read L1 overview, applies to directories.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI (must be a directory) |

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

**Response**

```json
{
  "status": "ok",
  "result": "## docs/\n\nContains API documentation and guides...",
  "time": 0.1
}
```

---

### read()

Read L2 full content.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI |

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

**Response**

```json
{
  "status": "ok",
  "result": "# API Documentation\n\nFull content of the file...",
  "time": 0.1
}
```

---

### ls()

List directory contents.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI |
| simple | bool | No | False | Return only relative paths |
| recursive | bool | No | False | List all subdirectories recursively |

**Entry Structure**

```python
{
    "name": "docs",           # File/directory name
    "size": 4096,             # Size in bytes
    "mode": 16877,            # File mode
    "modTime": "2024-01-01T00:00:00Z",  # ISO timestamp
    "isDir": True,            # True if directory
    "uri": "ctx://resources/docs/",  # Ctx URI
    "meta": {}                # Optional metadata
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
# Basic listing
curl -X GET "http://localhost:1933/api/v1/fs/ls?uri=ctx://resources/" \
  -H "X-API-Key: your-key"

# Simple path list
curl -X GET "http://localhost:1933/api/v1/fs/ls?uri=ctx://resources/&simple=true" \
  -H "X-API-Key: your-key"

# Recursive listing
curl -X GET "http://localhost:1933/api/v1/fs/ls?uri=ctx://resources/&recursive=true" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
atom_ctx ls ctx://resources/ [--simple] [--recursive]
```

**Response**

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

Get directory tree structure.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI |

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

**Response**

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

Get file or directory status information.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI |

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

**Response**

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

Create a directory.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI for the new directory |

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

**Response**

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

Remove file or directory.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI to remove |
| recursive | bool | No | False | Remove directory recursively |

**Python SDK (Embedded / HTTP)**

```python
# Remove single file
client.rm("ctx://resources/docs/old.md")

# Remove directory recursively
client.rm("ctx://resources/old-project/", recursive=True)
```

**HTTP API**

```
DELETE /api/v1/fs?uri={uri}&recursive={bool}
```

```bash
# Remove single file
curl -X DELETE "http://localhost:1933/api/v1/fs?uri=ctx://resources/docs/old.md" \
  -H "X-API-Key: your-key"

# Remove directory recursively
curl -X DELETE "http://localhost:1933/api/v1/fs?uri=ctx://resources/old-project/&recursive=true" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
atom_ctx rm ctx://resources/old.md [--recursive]
```

**Response**

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

Move file or directory.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| from_uri | str | Yes | - | Source Ctx URI |
| to_uri | str | Yes | - | Destination Ctx URI |

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

**Response**

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

Search content by pattern.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI to search in |
| pattern | str | Yes | - | Search pattern (regex) |
| case_insensitive | bool | No | False | Ignore case |

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

**Response**

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

Match files by pattern.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| pattern | str | Yes | - | Glob pattern (e.g., `**/*.md`) |
| uri | str | No | "ctx://" | Starting URI |

**Python SDK (Embedded / HTTP)**

```python
# Find all markdown files
results = client.glob("**/*.md", "ctx://resources/")
print(f"Found {results['count']} markdown files:")
for uri in results['matches']:
    print(f"  {uri}")

# Find all Python files
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

**Response**

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

Create relations between resources.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| from_uri | str | Yes | - | Source URI |
| uris | str or List[str] | Yes | - | Target URI(s) |
| reason | str | No | "" | Reason for the link |

**Python SDK (Embedded / HTTP)**

```python
# Single link
client.link(
    "ctx://resources/docs/auth/",
    "ctx://resources/docs/security/",
    reason="Security best practices for authentication"
)

# Multiple links
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
# Single link
curl -X POST http://localhost:1933/api/v1/relations/link \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "from_uri": "ctx://resources/docs/auth/",
    "to_uris": "ctx://resources/docs/security/",
    "reason": "Security best practices for authentication"
  }'

# Multiple links
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

**Response**

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

Get relations for a resource.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI |

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

**Response**

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

Remove a relation.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| from_uri | str | Yes | - | Source URI |
| uri | str | Yes | - | Target URI to unlink |

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

**Response**

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

## Related Documentation

- [Ctx URI](../concepts/04-ctx-uri.md) - URI specification
- [Context Layers](../concepts/03-context-layers.md) - L0/L1/L2
- [Resources](02-resources.md) - Resource management
