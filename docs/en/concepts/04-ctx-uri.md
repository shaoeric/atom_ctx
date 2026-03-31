# Ctx URI

Ctx URI is the unified resource identifier for all content in AtomCtx.

## Format

```
ctx://{scope}/{path}
```

- **scheme**: Always `ctx`
- **scope**: Top-level namespace (resources, user, agent, session, queue)
- **path**: Resource path within the scope

## Scopes

| Scope | Description | Lifecycle | Visibility |
|-------|-------------|-----------|------------|
| **resources** | Independent resources | Long-term | Global |
| **user** | User-level data | Long-term | Global |
| **agent** | Agent-level data | Long-term | Global |
| **session** | Session-level data | Session lifetime | Current session |
| **queue** | Processing queue | Temporary | Internal |
| **temp** | Temporary files | During parsing | Internal |

## Initial Directory Structure

Moving away from traditional flat database thinking, all context is organized as a filesystem. Agents no longer just find data through vector search, but can locate and browse data through deterministic paths and standard filesystem commands. Each context or directory is assigned a unique URI identifier string in the format ctx://{scope}/{path}, allowing the system to precisely locate and access resources stored in different locations.

```
ctx://
├── session/{session_id}/
│   ├── .abstract.md          # L0: One-line session summary
│   ├── .overview.md          # L1: Session overview
│   ├── .meta.json            # Session metadata
│   ├── messages.json         # Structured message storage
│   ├── checkpoints/          # Version snapshots
│   ├── summaries/            # Compression summary history
│   └── .relations.json       # Relations table
│
├── user/
│   ├── .abstract.md          # L0: Content summary
│   ├── .overview.md          # User profile
│   └── memories/             # User memory storage
│       ├── .overview.md      # Memory overview
│       ├── preferences/      # User preferences
│       ├── entities/         # Entity memories
│       └── events/           # Event records
│
├── agent/
│   ├── .abstract.md          # L0: Content summary
│   ├── .overview.md          # Agent overview
│   ├── memories/             # Agent learning memories
│   │   ├── .overview.md
│   │   ├── cases/            # Cases
│   │   └── patterns/         # Patterns
│   ├── instructions/         # Agent instructions
│   └── skills/               # Skills directory
│
└── resources/{project}/      # Resource workspace
```

## URI Examples

### Resources

```
ctx://resources/                           # All resources
ctx://resources/my-project/                # Project root
ctx://resources/my-project/docs/           # Docs directory
ctx://resources/my-project/docs/api.md     # Specific file
```

### User Data

```
ctx://user/                                # User root
ctx://user/memories/                       # All user memories
ctx://user/memories/preferences/           # User preferences
ctx://user/memories/preferences/coding     # Specific preference
ctx://user/memories/entities/              # Entity memories
ctx://user/memories/events/                # Event memories
```

### Agent Data

```
ctx://agent/                               # Agent root
ctx://agent/skills/                        # All skills
ctx://agent/skills/search-web              # Specific skill
ctx://agent/memories/                      # Agent memories
ctx://agent/memories/cases/                # Learned cases
ctx://agent/memories/patterns/             # Learned patterns
ctx://agent/instructions/                  # Agent instructions
```

### Session Data

```
ctx://session/{session_id}/                # Session root
ctx://session/{session_id}/messages/       # Session messages
ctx://session/{session_id}/tools/          # Tool executions
ctx://session/{session_id}/history/        # Archived history
```

## Directory Structure

```
ctx://
├── resources/       # Independent resources
│   └── {project}/
│       ├── .abstract.md
│       ├── .overview.md
│       └── {files...}
│
├── user/{user_id}/
│   ├── profile.md                # User basic info
│   └── memories/
│       ├── preferences/          # By topic
│       ├── entities/             # Each independent
│       └── events/               # Each independent
│
├── agent/{agent_space}/          # agent_space is derived from memory.agent_scope_mode
│   ├── skills/                   # Skill definitions
│   ├── memories/
│   │   ├── cases/
│   │   └── patterns/
│   ├── workspaces/
│   └── instructions/
│
└── session/{user_space}/{session_id}/
    ├── messages/
    ├── tools/
    └── history/
```

The `agent_space` value depends on `memory.agent_scope_mode`:

- `user+agent` (default): `agent_space = md5(f"{user_id}:{agent_id}")[:12]`
- `agent`: `agent_space = md5(agent_id)[:12]`

## URI Operations

### Parsing

```python
from atom_ctx_cli.utils.uri import CtxURI

uri = CtxURI("ctx://resources/docs/api")
print(uri.scope)      # "resources"
print(uri.full_path)  # "resources/docs/api"
```

### Building

```python
# Join paths
base = "ctx://resources/docs/"
full = CtxURI(base).join("api.md").uri  # ctx://resources/docs/api.md

# Parent directory
uri = "ctx://resources/docs/api.md"
parent = CtxURI(uri).parent.uri  # ctx://resources/docs
```

## API Usage

### Targeting Specific Scopes

```python
# Search only in resources
results = client.find(
    "authentication",
    target_uri="ctx://resources/"
)

# Search only in user memories
results = client.find(
    "coding preferences",
    target_uri="ctx://user/memories/"
)

# Search only in skills
results = client.find(
    "web search",
    target_uri="ctx://agent/skills/"
)
```

### File System Operations

```python
# List directory
entries = await client.ls("ctx://resources/")

# Read file
content = await client.read("ctx://resources/docs/api.md")

# Get abstract
abstract = await client.abstract("ctx://resources/docs/")

# Get overview
overview = await client.overview("ctx://resources/docs/")
```

## Special Files

Each directory may contain special files:

| File | Purpose |
|------|---------|
| `.abstract.md` | L0 abstract (~100 tokens) |
| `.overview.md` | L1 overview (~2k tokens) |
| `.relations.json` | Related resources |
| `.meta.json` | Metadata |

## Best Practices

### Use Trailing Slash for Directories

```python
# Directory
"ctx://resources/docs/"

# File
"ctx://resources/docs/api.md"
```

### Scope-Specific Operations

```python
# Add resources only to resources scope
await client.add_resource(url, target="ctx://resources/project/")

# Skills go to agent scope
await client.add_skill(skill)  # Automatically to ctx://agent/skills/
```

## Related Documents

- [Architecture Overview](./01-architecture.md) - System architecture
- [Context Types](./02-context-types.md) - Three types of context
- [Context Layers](./03-context-layers.md) - L0/L1/L2 model
- [Storage Architecture](./05-storage.md) - VikingFS and AGFS
- [Session Management](./08-session.md) - Session storage structure
