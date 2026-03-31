---
name: atom_ctx
description: "Activate when the user asks about any repository listed in the system prompt under 'AtomCtx — Indexed Code Repositories', or when they ask about an external library, framework, or project that may have been indexed. Also activate when the user wants to add, remove, or manage repos. Always search the local codebase first before using this skill."
license: MIT
compatibility: opencode
---

# AtomCtx Code Repository Search

**IMPORTANT: All `ctx` commands are terminal (shell) commands — run them via the `bash` tool. Execute directly — no pre-checks, no test commands. Handle errors when they occur.**

## How AtomCtx Organizes Data

AtomCtx stores content in a virtual filesystem under the `ctx://` namespace. Each URI maps to a file or directory, e.g. `ctx://resources/fastapi/routing.py`. Each directory has AI-generated summaries (`abstract` / `overview`). **The key principle: narrow the URI scope to improve retrieval efficiency.** Instead of searching all repos, lock to a specific repo or subdirectory — this reduces noise and speeds up results significantly.

## Search Commands

Choose the right command based on what you're looking for:

| Command | Use when | Example |
|---------|----------|---------|
| `ctx search` | Semantic search — use for concept/intent based queries | "dependency injection", "how auth works" |
| `ctx grep` | You know the **exact keyword or symbol** | function name, class name, error string |
| `ctx glob` | You want to **enumerate files** by pattern | all `*.py` files, all test files |

```bash
# Semantic search
ctx search "dependency injection" --uri ctx://resources/fastapi --limit 10
ctx search "how tokens are refreshed" --uri ctx://resources/fastapi/fastapi/security
ctx search "JWT authentication" --limit 10          # across all repos
ctx search "error handling" --limit 5 --threshold 0.7  # filter low-relevance results

# Keyword search — exact match or regex
ctx grep "verify_token" --uri ctx://resources/fastapi
ctx grep "class.*Session" --uri ctx://resources/requests/requests

# File enumeration — by name pattern (always specify --uri to scope the search)
ctx glob "**/*.py" --uri ctx://resources/fastapi
ctx glob "**/test_*.py" --uri ctx://resources/fastapi/tests
ctx glob "**/*.py" --uri ctx://resources/   # across all repos
```

**Narrowing scope:** once you identify a relevant directory, pass it as `--uri` to restrict subsequent searches to that subtree — this is faster and more precise than searching the whole repo.

**Query formulation:** write specific, contextual queries rather than single keywords.
```bash
ctx search "API"                                                       # too vague
ctx search "REST API authentication with JWT tokens"                   # better
ctx search "JWT token refresh flow" --uri ctx://resources/backend   # best
```

## Read Content

```bash
# Directories: AI-generated summaries
ctx abstract ctx://resources/fastapi/fastapi/dependencies/   # one-line summary
ctx overview ctx://resources/fastapi/fastapi/dependencies/   # detailed breakdown

# Files: raw content
ctx read ctx://resources/fastapi/fastapi/dependencies/utils.py
ctx read ctx://resources/fastapi/fastapi/dependencies/utils.py --offset 100 --limit 50
```

`abstract` / `overview` only work on directories. `read` only works on files.

## Browse

```bash
ctx ls ctx://resources/                        # list all indexed repos
ctx ls ctx://resources/fastapi                 # list repo top-level contents
ctx ls ctx://resources/fastapi --simple        # paths only, no metadata
ctx ls ctx://resources/fastapi --recursive     # list all files recursively
ctx tree ctx://resources/fastapi               # full directory tree (default: 3 levels deep)
ctx tree ctx://resources/fastapi -L 2          # limit depth to 2 levels
ctx tree ctx://resources/fastapi -l 200        # truncate abstract column to 200 chars
ctx tree ctx://resources/fastapi -L 2 -l 200   # combined: 2 levels deep, 200-char summaries
```

`-L` controls how many levels deep the tree expands. `-l` controls the length of the AI-generated summary per directory. Use `ctx tree -L 2 -l 200` as a good starting point to understand a repo's structure before diving in.

## Add a Repository

```bash
ctx add-resource https://github.com/owner/repo --to ctx://resources/repo --timeout 300
```

`--timeout` is required (seconds). Use 300 (5 min) for small repos, increase for larger ones.

After submitting, run `ctx observer queue` once and report status to user. Indexing runs in background — do not poll or wait.

| Repo Size | Files | Est. Time |
|-----------|-------|-----------|
| Small | < 100 | 2–5 min |
| Medium | 100–500 | 5–20 min |
| Large | 500+ | 20–60+ min |

## Remove a Repository

```bash
ctx rm ctx://resources/fastapi --recursive
```

This permanently deletes the repo and all its indexed content. Confirm with the user before running.

## Error Handling

**`command not found: ov`** → Tell user: `pip install atom-ctx --upgrade`. Stop.

**`url is required` / `CLI_CONFIG` error** → Auto-create config and retry:
```bash
mkdir -p ~/.ctx && echo '{"url": "http://localhost:1933"}' > ~/.ctx/ctx-cli.conf
```

**`CONNECTION_ERROR` / failed to connect:**
- `~/.ctx/ctx.conf` **exists** → auto-start server, wait until healthy, retry:
  ```bash
  ctx-server > /tmp/ctx-server.log 2>&1 &
  for i in $(seq 1 10); do ctx health 2>/dev/null && break; sleep 3; done
  ```
- **Does not exist** → Tell user to configure `~/.ctx/ctx.conf` first. Stop.

## More Help

For other issues or command details, run:

```bash
ctx help
ctx <command> --help   # e.g. ctx search --help
```
