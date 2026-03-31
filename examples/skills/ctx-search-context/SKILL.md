---
name: ov-search-context
description: Search context data(memories, skills and resource) from AtomCtx Context Database (aka. ov). Trigger this tool when 1. need information that might be stored as memories, skills or resources on AtomCtx; 2. is explicitly requested searching files or knowledge; 3. sees `search context`, `search atom_ctx`, `search ov` request.
compatibility: CLI configured at `~/.ctx/ctx-cli.conf`
---
# AtomCtx (OV) context searching
The `ctx search` command performs context-aware retrieval across all memories and resources in AtomCtx — combining semantic understanding with directory recursive retrieval to find the most relevant context for any query.

## Table of Content
- When to Use
- Sub-commands for search
  - List directories (`ctx ls`)
  - Tree view (`ctx tree`)
  - Semantic Search (`ctx find`)
  - Content Pattern Search (`ctx grep`)
  - File Glob Search (`ctx glob`)
  - Full content read (`ctx read`)
  - Get overview (`ctx overview`)
  - Get Abstract (`ctx abstract`)
- Prerequisite

## When to Use

- Finding specific information within imported resources or saved memories
- Retrieving context about topics, APIs, or patterns previously added
- Searching across project documentation, code, and learnings
- When an agent needs to reference previously stored knowledge

> note: cli command can be outdated, when sees error, use `--help` to get latest usage

## Sub-commands for search

### List Contents (`ctx ls`)

Browse directory structure:

```bash
# List root directory
ctx ls

# List specific directory
ctx ls ctx://resources/my-project/docs/

# Simple path output (only uris, no metadata)
ctx ls ctx://resources --simple

# Show hidden files
ctx ls ctx://resources --all

# Control output limits (default 256)
ctx ls ctx://resources --node-limit 50

# Control abstract info length limit for each node (default 256)
ctx ls ctx://resources --abs-limit 128
```

### Tree View (`ctx tree`)

Visualize directory hierarchy:

```bash
# Show tree structure
ctx tree ctx://resources

# Control depth limits (default 3)
ctx tree ctx://resources --level-limit 2

# Control node limits
ctx tree ctx://resources --node-limit 100 --abs-limit 128

# Show all files including hidden
ctx tree ctx://resources --all
```

### Semantic find (`ctx find`)

Find method with semantic relevance ranking:

```bash
# Basic find across all context
ctx find "how to handle API rate limits"

# Find within specific URI scope
ctx find "authentication flow" --uri "ctx://resources/my-project"

# Limit results and set relevance score threshold
ctx find "error handling" --node-limit 5 --threshold 0.3
```

### Content Pattern Search (`ctx grep`)

Literal pattern matching:

```bash
# Find exact text pattern (Note: this is expensive, and suggest within specific small URI scope)
ctx grep "ctx://resources" "TODO:" --uri "ctx://resources/my-project"

# Case-insensitive search
ctx grep "ctx://resources" "API_KEY" --ignore-case --uri "ctx://resources/my-project"

# Limit results and set node limit
ctx grep "ctx://resources" "API_KEY" --node-limit 5 --uri "ctx://resources/my-project"
```

### File Glob Search (`ctx glob`)

File path pattern matching:

```bash
# Find all markdown files (Note: this is expensive, and suggest within specific small URI scope)
ctx glob "**/*.md" --uri "ctx://resources/my-project"

# Limit results and set node limit
ctx glob "**/*.md" --uri "ctx://resources/my-project" --node-limit 5
```

### Read File Content (`ctx read`)

Retrieve full content (L0-L2 layer):

```bash
# Read full content
ctx read ctx://resources/docs/api/api-1.md

# Read first 10 lines of api-2.md
ctx read ctx://resources/docs/api/api-2.md | head -n 10

# Read abstract (L0 - quick summary)
ctx abstract ctx://resources/docs/api/
ctx read ctx://resources/docs/api/.abstract.md

# Read overview (L1 - key points)
ctx overview ctx://resources/docs/api/
ctx read ctx://resources/docs/api/.overview.md
```

### Combining Search

Use search results to guide further actions:

```bash
ctx ls ctx://resources/

# Search for relevant files
ctx search "authentication" --uri "ctx://resources/project-A"

# Get overview for context
ctx overview ctx://resources/project-A/backend

# Decide to read specific content
ctx read ctx://resources/project-A/backend/auth.md
```

## Prerequisites

- CLI configured: `~/.ctx/ctx-cli.conf`
- Resources or memories previously added to AtomCtx
