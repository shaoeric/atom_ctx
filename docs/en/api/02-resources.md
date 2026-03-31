# Resources

Resources are external knowledge that agents can reference. This guide covers how to add, manage, and retrieve resources.

## Supported Formats

| Format | Extensions | Processing |
|--------|------------|------------|
| PDF | `.pdf` | Text and image extraction |
| Markdown | `.md` | Native support |
| HTML | `.html`, `.htm` | Cleaned text extraction |
| Plain Text | `.txt` | Direct import |
| JSON/YAML | `.json`, `.yaml`, `.yml` | Structured parsing |
| Code | `.py`, `.js`, `.ts`, `.go`, `.java`, etc. | Syntax-aware parsing |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` | VLM description |
| Video | `.mp4`, `.mov`, `.avi` | Frame extraction + VLM |
| Audio | `.mp3`, `.wav`, `.m4a` | Transcription |
| Documents | `.docx` | Text extraction |
| Feishu/Lark | URL (`*.feishu.cn`, `*.larksuite.com`) | Cloud document parsing via `lark-oapi` |

## Processing Pipeline

```
Input -> Parser -> TreeBuilder -> AGFS -> SemanticQueue -> Vector Index
```

1. **Parser**: Extracts content based on file type
2. **TreeBuilder**: Creates directory structure
3. **AGFS**: Stores files in virtual file system
4. **SemanticQueue**: Generates L0/L1 asynchronously
5. **Vector Index**: Indexes for semantic search

## API Reference

### add_resource()

Add a resource to the knowledge base.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| path | str | Yes | - | SDK/CLI: local path, directory path, or URL. Raw HTTP: remote URL only |
| temp_file_id | str | No | None | Upload ID returned by `POST /api/v1/resources/temp_upload` for raw HTTP local file ingestion |
| target | str | No | None | Target Ctx URI (must be in `resources` scope) |
| reason | str | No | "" | Why this resource is being added (improves search relevance) |
| instruction | str | No | "" | Special processing instructions |
| wait | bool | No | False | Wait for semantic processing to complete |
| timeout | float | No | None | Timeout in seconds (only used when wait=True) |
| watch_interval | float | No | 0 | Watch interval (minutes). >0 enables/updates watch; <=0 disables watch. Only takes effect when target is provided |

**How local files and directories work**

- Python SDK and CLI accept local file and directory paths directly. In HTTP mode they automatically upload local files before calling the server API.
- Raw HTTP callers should think in two categories:
  - Remote source: pass `path` directly, for example `https://example.com/doc.pdf`
  - Local file: call `POST /api/v1/resources/temp_upload` first, then pass the returned `temp_file_id`
  - Local directory: zip it first, upload the `.zip` file, then pass the returned `temp_file_id`
- `POST /api/v1/resources` does not accept direct host filesystem paths such as `./guide.md`, `/tmp/guide.md`, or `/tmp/my-dir/`.

**Incremental Updates**

When you call `add_resource()` repeatedly for the same resource URI, the system performs an incremental update instead of rebuilding everything from scratch:

- **Trigger**: `target` is provided and already exists in the knowledge base.
- **High-level idea**: each ingestion first builds a temporary resource tree from the new input. During asynchronous semantic processing, the temporary tree is compared against the existing tree at `target`, and only the changed parts are re-processed and synchronized.
- **Incremental behavior in the semantic stage**:
  - **Unchanged files**: reuse existing L0 summaries and vector index records; skip vectorization.
  - **Changed files**: regenerate summaries and vector index entries.
  - **Directory-level L0/L1 (abstract/overview)**: if the child set and their change status are unchanged, reuse existing results and skip vectorization; otherwise recompute and update.
- **Filesystem + index sync**: after the semantic DAG finishes, a top-down diff is applied from the temporary tree to `target` to synchronize additions, deletions, and updates. Vector store records are kept consistent: deletions remove corresponding vectors, while moves/overwrites update vector records’ URI mapping, completing an incremental update of both the resource tree and the semantic index.

**Python SDK (Embedded / HTTP)**

```python
result = client.add_resource(
    "./documents/guide.md",
    reason="User guide documentation"
)
print(f"Added: {result['root_uri']}")

client.wait_processed()
```

**HTTP API**

```
POST /api/v1/resources
```

```bash
curl -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "path": "https://example.com/guide.md",
    "reason": "User guide documentation"
  }'
```

**CLI**

```bash
atom_ctx add-resource ./documents/guide.md --reason "User guide documentation"
```

**Response**

```json
{
  "status": "ok",
  "result": {
    "status": "success",
    "root_uri": "ctx://resources/documents/guide.md",
    "source_path": "./documents/guide.md",
    "errors": []
  },
  "time": 0.1
}
```

**Example: Add from URL**

**Python SDK (Embedded / HTTP)**

```python
result = client.add_resource(
    "https://example.com/api-docs.md",
    target="ctx://resources/external/",
    reason="External API documentation"
)
client.wait_processed()
```

**HTTP API**

```bash
curl -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "path": "https://example.com/api-docs.md",
    "target": "ctx://resources/external/",
    "reason": "External API documentation",
    "wait": true
  }'
```

**CLI**

```bash
atom_ctx add-resource https://example.com/api-docs.md --to ctx://resources/external/ --reason "External API documentation"
```

**Example: Add a Local File with Raw HTTP**

When you call the HTTP API directly, upload local files first and then use `temp_file_id`.

```bash
# Step 1: upload the local file
TEMP_FILE_ID=$(
  curl -sS -X POST http://localhost:1933/api/v1/resources/temp_upload \
    -H "X-API-Key: your-key" \
    -F 'file=@./documents/guide.md' \
  | jq -r '.result.temp_file_id'
)

# Step 2: add the uploaded file
curl -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d "{
    \"temp_file_id\": \"$TEMP_FILE_ID\",
    \"reason\": \"User guide documentation\",
    \"wait\": true
  }"
```

**Example: Add a Local Directory with Raw HTTP**

When you call the HTTP API directly, zip the directory yourself first. CLI and SDK do this automatically for you.

```bash
# Step 1: zip the local directory
cd ./documents
zip -r /tmp/guide.zip ./guide

# Step 2: upload the zip file
TEMP_FILE_ID=$(
  curl -sS -X POST http://localhost:1933/api/v1/resources/temp_upload \
    -H "X-API-Key: your-key" \
    -F 'file=@/tmp/guide.zip' \
  | jq -r '.result.temp_file_id'
)

# Step 3: add the uploaded directory archive
curl -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d "{
    \"temp_file_id\": \"$TEMP_FILE_ID\",
    \"reason\": \"Import local directory\",
    \"wait\": true
  }"
```

**Example: Add Feishu/Lark Cloud Documents**

[Feishu](https://www.feishu.cn) (飞书) and its international version [Lark](https://www.larksuite.com) are widely used for documentation in Chinese tech companies. AtomCtx can directly import cloud documents by URL.

Supported document types:

| Type | URL Pattern |
|------|-------------|
| Documents | `https://*.feishu.cn/docx/{id}` |
| Wiki pages | `https://*.feishu.cn/wiki/{token}` |
| Spreadsheets | `https://*.feishu.cn/sheets/{token}` |
| Bitable | `https://*.feishu.cn/base/{token}` |

> **Setup**: Install the optional dependency: `pip install 'atom-ctx[bot-feishu]'`
>
> Configure credentials via `ctx.conf` (see [Configuration](../../guides/01-configuration.md#feishu)) or environment variables:
> ```bash
> export FEISHU_APP_ID="cli_xxx"
> export FEISHU_APP_SECRET="xxx"
> ```

**Python SDK (Embedded / HTTP)**

```python
# Import a Feishu document
result = client.add_resource(
    "https://example.feishu.cn/docx/doxcnABC123",
    reason="Project design document"
)
client.wait_processed()

# Import a wiki page (auto-resolves to underlying type)
client.add_resource("https://example.feishu.cn/wiki/wikiXYZ")

# Import a spreadsheet
client.add_resource("https://example.feishu.cn/sheets/shtcn456")
```

**CLI**

```bash
# Import a Feishu document
atom_ctx add-resource "https://example.feishu.cn/docx/doxcnABC123" --reason "Project design document"

# Import a wiki page
atom_ctx add-resource "https://example.feishu.cn/wiki/wikiXYZ"

# Incremental update to an existing target
atom_ctx add-resource "https://example.feishu.cn/docx/doxcnABC123" --to ctx://resources/design-doc
```

**Example: Wait for Processing**

**Python SDK (Embedded / HTTP)**

```python
# Option 1: Wait inline
result = client.add_resource("./documents/guide.md", wait=True)
print(f"Queue status: {result['queue_status']}")

# Option 2: Wait separately (for batch processing)
client.add_resource("./file1.md")
client.add_resource("./file2.md")
client.add_resource("./file3.md")

status = client.wait_processed()
print(f"All processed: {status}")
```

**HTTP API**

```bash
# Wait inline
curl -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"path": "https://example.com/guide.md", "wait": true}'

# Wait separately after batch
curl -X POST http://localhost:1933/api/v1/system/wait \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{}'
```

**CLI**

```bash
atom_ctx add-resource ./documents/guide.md --wait
```

**Example: Watch for Updates (watch_interval)**

`watch_interval` is in minutes and periodically triggers re-processing for the specified target URI:

- `watch_interval > 0`: create (or reactivate and update) a watch task for the `target`
- `watch_interval <= 0`: disable (deactivate) the watch task for the `target`
- watch tasks are only managed when `target` / CLI `--to` is provided

If there is already an active watch task for the same `target`, submitting another request with `watch_interval > 0` returns a conflict error. Disable it first (`watch_interval = 0`) and then set a new interval.

**Python SDK (Embedded / HTTP)**

```python
client.add_resource(
    "./documents/guide.md",
    target="ctx://resources/documents/guide.md",
    watch_interval=60,
)
```

**HTTP API**

```bash
curl -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "path": "https://example.com/guide.md",
    "target": "ctx://resources/documents/guide.md",
    "watch_interval": 60
  }'
```

**CLI**

```bash
atom_ctx add-resource ./documents/guide.md --to ctx://resources/documents/guide.md --watch-interval 60

# Disable watch
atom_ctx add-resource ./documents/guide.md --to ctx://resources/documents/guide.md --watch-interval 0
```

---

### export_ctxpack()

Export a resource tree as a `.ctxpack` file.

**Parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| uri | str | Yes | - | Ctx URI to export |
| to | str | Yes | - | Target file path |

**Python SDK (Embedded / HTTP)**

```python
path = client.export_ctxpack(
    "ctx://resources/my-project/",
    "./exports/my-project.ctxpack"
)
print(f"Exported to: {path}")
```

**HTTP API**

```
POST /api/v1/pack/export
```

```bash
curl -X POST http://localhost:1933/api/v1/pack/export \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "uri": "ctx://resources/my-project/",
    "to": "./exports/my-project.ctxpack"
  }'
```

**CLI**

```bash
atom_ctx export ctx://resources/my-project/ ./exports/my-project.ctxpack
```

**Response**

```json
{
  "status": "ok",
  "result": {
    "file": "./exports/my-project.ctxpack"
  },
  "time": 0.1
}
```

---

### import_ctxpack()

Import a `.ctxpack` file.

**SDK / CLI parameters**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| file_path | str | Yes | - | Local `.ctxpack` file path |
| parent | str | Yes | - | Target parent URI |
| force | bool | No | False | Overwrite existing resources |
| vectorize | bool | No | True | Trigger vectorization after import |

**Raw HTTP request body**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| temp_file_id | str | Yes | - | Upload ID returned by `POST /api/v1/resources/temp_upload` |
| parent | str | Yes | - | Target parent URI |
| force | bool | No | False | Overwrite existing resources |
| vectorize | bool | No | True | Trigger vectorization after import |

**Python SDK (Embedded / HTTP)**

```python
uri = client.import_ctxpack(
    "./exports/my-project.ctxpack",
    "ctx://resources/imported/",
    force=True,
    vectorize=True
)
print(f"Imported to: {uri}")

client.wait_processed()
```

**HTTP API**

```
POST /api/v1/pack/import
```

```bash
# Step 1: upload the local ctxpack file
TEMP_FILE_ID=$(
  curl -sS -X POST http://localhost:1933/api/v1/resources/temp_upload \
    -H "X-API-Key: your-key" \
    -F 'file=@./exports/my-project.ctxpack' \
  | jq -r '.result.temp_file_id'
)

# Step 2: import using temp_file_id
curl -X POST http://localhost:1933/api/v1/pack/import \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d "{
    \"temp_file_id\": \"$TEMP_FILE_ID\",
    \"parent\": \"ctx://resources/imported/\",
    \"force\": true,
    \"vectorize\": true
  }"
```

**CLI**

```bash
atom_ctx import ./exports/my-project.ctxpack ctx://resources/imported/ --force
```

**Response**

```json
{
  "status": "ok",
  "result": {
    "uri": "ctx://resources/imported/my-project/"
  },
  "time": 0.1
}
```

---

## Managing Resources

### List Resources

**Python SDK (Embedded / HTTP)**

```python
# List all resources
entries = client.ls("ctx://resources/")

# List with details
for entry in entries:
    type_str = "dir" if entry['isDir'] else "file"
    print(f"{entry['name']} - {type_str}")

# Simple path list
paths = client.ls("ctx://resources/", simple=True)
# Returns: ["project-a/", "project-b/", "shared/"]

# Recursive listing
all_entries = client.ls("ctx://resources/", recursive=True)
```

**HTTP API**

```
GET /api/v1/fs/ls?uri={uri}&simple={bool}&recursive={bool}
```

```bash
# List all resources
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
# List all resources
atom_ctx ls ctx://resources/

# Simple path list
atom_ctx ls ctx://resources/ --simple

# Recursive listing
atom_ctx ls ctx://resources/ --recursive
```

**Response**

```json
{
  "status": "ok",
  "result": [
    {
      "name": "project-a",
      "size": 4096,
      "isDir": true,
      "uri": "ctx://resources/project-a/"
    }
  ],
  "time": 0.1
}
```

---

### Read Resource Content

**Python SDK (Embedded / HTTP)**

```python
# L0: Abstract
abstract = client.abstract("ctx://resources/docs/")

# L1: Overview
overview = client.overview("ctx://resources/docs/")

# L2: Full content
content = client.read("ctx://resources/docs/api.md")
```

**HTTP API**

```bash
# L0: Abstract
curl -X GET "http://localhost:1933/api/v1/content/abstract?uri=ctx://resources/docs/" \
  -H "X-API-Key: your-key"

# L1: Overview
curl -X GET "http://localhost:1933/api/v1/content/overview?uri=ctx://resources/docs/" \
  -H "X-API-Key: your-key"

# L2: Full content
curl -X GET "http://localhost:1933/api/v1/content/read?uri=ctx://resources/docs/api.md" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
# L0: Abstract
atom_ctx abstract ctx://resources/docs/

# L1: Overview
atom_ctx overview ctx://resources/docs/

# L2: Full content
atom_ctx read ctx://resources/docs/api.md
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

### Move Resources

**Python SDK (Embedded / HTTP)**

```python
client.mv(
    "ctx://resources/old-project/",
    "ctx://resources/new-project/"
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
    "from_uri": "ctx://resources/old-project/",
    "to_uri": "ctx://resources/new-project/"
  }'
```

**CLI**

```bash
atom_ctx mv ctx://resources/old-project/ ctx://resources/new-project/
```

**Response**

```json
{
  "status": "ok",
  "result": {
    "from": "ctx://resources/old-project/",
    "to": "ctx://resources/new-project/"
  },
  "time": 0.1
}
```

---

### Delete Resources

**Python SDK (Embedded / HTTP)**

```python
# Delete single file
client.rm("ctx://resources/docs/old.md")

# Delete directory recursively
client.rm("ctx://resources/old-project/", recursive=True)
```

**HTTP API**

```
DELETE /api/v1/fs?uri={uri}&recursive={bool}
```

```bash
# Delete single file
curl -X DELETE "http://localhost:1933/api/v1/fs?uri=ctx://resources/docs/old.md" \
  -H "X-API-Key: your-key"

# Delete directory recursively
curl -X DELETE "http://localhost:1933/api/v1/fs?uri=ctx://resources/old-project/&recursive=true" \
  -H "X-API-Key: your-key"
```

**CLI**

```bash
# Delete single file
atom_ctx rm ctx://resources/docs/old.md

# Delete directory recursively
atom_ctx rm ctx://resources/old-project/ --recursive
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

### Create Links

**Python SDK (Embedded / HTTP)**

```python
# Link related resources
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

### Get Relations

**Python SDK (Embedded / HTTP)**

```python
relations = client.relations("ctx://resources/docs/auth/")
for rel in relations:
    print(f"{rel['uri']}: {rel['reason']}")
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

### Remove Links

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

## Best Practices

### Organize by Project

```
ctx://resources/
+-- project-a/
|   +-- docs/
|   +-- specs/
|   +-- references/
+-- project-b/
|   +-- ...
+-- shared/
    +-- common-docs/
```

## Related Documentation

- [Retrieval](06-retrieval.md) - Search resources
- [File System](03-filesystem.md) - File operations
- [Context Types](../concepts/02-context-types.md) - Resource concept
