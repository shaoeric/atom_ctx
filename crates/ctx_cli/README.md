# AtomCtx CLI

Command-line interface for [AtomCtx](https://github.com/volcengine/atom-ctx) - an Agent-native context database.

## Installation

### Quick Install (Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/volcengine/AtomCtx/main/crates/ctx_cli/install.sh | bash
```

### From Source

```bash
# atom_ctx need rust >= 1.88, please upgrade it if necessary
# brew upgrade rust
cargo install --path crates/ctx_cli
```

## Configuration

Create `~/.ctx/ctx-cli.conf`:

```json
{
  "url": "http://localhost:1933",
  "api_key": "your-api-key",
  "account": "acme",
  "user": "alice",
  "agent_id": "assistant-1"
}
```

`account` and `user` are optional with a regular user key because the server can derive them from the key. They are recommended when you use `trusted` auth mode or a root key against tenant-scoped APIs.

## Quick Start

```bash
# Add a resource
ctx add-resource https://raw.githubusercontent.com/volcengine/AtomCtx/refs/heads/main/docs/en/about/01-about-us.md --wait

# List contents
ctx ls ctx://resources

# Semantic search
ctx find "what is atom_ctx"

# Get file tree
ctx tree ctx://resources

# Read content
ctx read ctx://resources/...
```

## Command Groups

### Resource Management
- `add-resource` - Import local files or URLs
- `add-skill` - Add a skill
- `export` - Export as .ctxpack
- `import` - Import .ctxpack

### Relations
- `relations` - List relations
- `link` - Create relation links
- `unlink` - Remove relation

### Filesystem
- `ls` - List directory contents
- `tree` - Get directory tree
- `mkdir` - Create directory
- `rm` - Remove resource
- `mv` - Move/rename
- `stat` - Get metadata

### Content Access
- `read` - Read L2 (full content)
- `abstract` - Read L0 (abstract)
- `overview` - Read L1 (overview)

### Search
- `find` - Semantic retrieval
- `search` - Context-aware retrieval
- `grep` - Content pattern search
- `glob` - File glob pattern

### System
- `system wait` - Wait for async processing
- `system status` - Component status
- `system health` - Health check
- `observer queue` - Queue status
- `observer vikingdb` - VikingDB status
- `observer vlm` - VLM status

### Session
- `session new` - Create session
- `session list` - List sessions
- `session get` - Get session details
- `session delete` - Delete session
- `session add-message` - Add message
- `session commit` - Commit and extract memories

### Config
- `config show` - Show configuration
- `config validate` - Validate config

## Output Formats

```bash
ctx --output json ls
ctx --output table ls
ctx -o json ls  # Compact JSON wrapper for scripts
```

## Examples

```bash
# Add URL and wait for processing
ctx add-resource https://example.com/docs --wait --timeout 60

# Add local directory with advanced options
ctx add-resource ./dir \
  --wait --timeout 600 \
  --ignore-dirs "subdir-a,subdir-b/subsubdir-c" \
  --exclude "*.tmp,*.log"

# Search with threshold
ctx find "API authentication" --threshold 0.7 --limit 5

# Recursive list
ctx ls ctx://resources --recursive

# Temporarily override identity from CLI flags
ctx --account acme --user alice --agent-id assistant-2 ls ctx://

# Glob search
ctx glob "**/*.md" --uri ctx://resources

# Session workflow
SESSION=$(ov -o json session new | jq -r '.result.session_id')
ctx session add-message --session-id $SESSION --role user --content "Hello"
ctx session commit --session-id $SESSION
```

## Development

```bash
# Build
cargo build --release

# Run tests
cargo test

# Install locally
cargo install --path .
```
