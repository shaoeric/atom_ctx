# AtomCtx Memory Plugin for OpenCode

OpenCode plugin example that exposes AtomCtx memories as explicit tools and automatically syncs conversation sessions into AtomCtx.

Chinese install guide: [INSTALL-ZH.md](./INSTALL-ZH.md)

## Mechanism

This example uses OpenCode's tool mechanism to expose AtomCtx capabilities as explicit agent-callable tools.

In practice, that means:

- the agent sees concrete tools and decides when to call them
- AtomCtx data is fetched on demand through tool execution instead of being pre-injected into every prompt
- the plugin also keeps an AtomCtx session in sync with the OpenCode conversation and triggers background memory extraction with `memcommit`

This example focuses on explicit memory access, filesystem-style browsing, and session-to-memory synchronization inside OpenCode.

## What It Does

- Exposes four memory tools for OpenCode agents:
  - `memsearch`
  - `memread`
  - `membrowse`
  - `memcommit`
- Automatically maps each OpenCode session to an AtomCtx session
- Streams user and assistant messages into AtomCtx
- Uses background `commit` tasks to avoid repeated synchronous timeout failures
- Persists local runtime state for reconnect and recovery

## Files

This example contains:

- `atom_ctx-memory.ts`: the plugin implementation used by OpenCode
- `atom_ctx-config.example.json`: template config
- `.gitignore`: ignores local runtime files after you copy the example into a workspace

## Prerequisites

- OpenCode
- AtomCtx HTTP Server
- A valid AtomCtx API key if your server requires authentication

Start the server first if it is not already running:

```bash
ctx-server --config ~/.ctx/ctx.conf
```

## Install Into OpenCode

Recommended location from the OpenCode docs:

```bash
~/.config/opencode/plugins
```

Install with:

```bash
mkdir -p ~/.config/opencode/plugins
cp examples/opencode-memory-plugin/atom_ctx-memory.ts ~/.config/opencode/plugins/atom_ctx-memory.ts
cp examples/opencode-memory-plugin/atom_ctx-config.example.json ~/.config/opencode/plugins/atom_ctx-config.json
cp examples/opencode-memory-plugin/.gitignore ~/.config/opencode/plugins/.gitignore
```

Then edit `~/.config/opencode/plugins/atom_ctx-config.json`.

OpenCode auto-discovers first-level `*.ts` and `*.js` files under `~/.config/opencode/plugins`, so no explicit `plugin` entry is required in `~/.config/opencode/opencode.json`.

This plugin also works if you intentionally place it in a workspace-local plugin directory, because it stores config and runtime files next to the plugin file itself.

Recommended: provide the API key via environment variable instead of writing it into the config file:

```bash
export ATOM_CTX_API_KEY="your-api-key-here"
```

## Configuration

Example config:

```json
{
  "endpoint": "http://localhost:1933",
  "apiKey": "",
  "enabled": true,
  "timeoutMs": 30000,
  "autoCommit": {
    "enabled": true,
    "intervalMinutes": 10
  }
}
```

The environment variable `ATOM_CTX_API_KEY` takes precedence over the config file.

## Runtime Files

After installation, the plugin creates these local files next to the plugin file:

- `atom_ctx-config.json`
- `atom_ctx-memory.log`
- `atom_ctx-session-map.json`

These are runtime artifacts and should not be committed.

## Tools

### `memsearch`

Unified search across memories, resources, and skills.

Parameters:

- `query`: search query
- `target_uri?`: narrow search to a URI prefix such as `ctx://user/memories/`
- `mode?`: `auto | fast | deep`
- `limit?`: max results
- `score_threshold?`: optional minimum score

### `memread`

Read content from a specific `ctx://` URI.

Parameters:

- `uri`: target URI
- `level?`: `auto | abstract | overview | read`

### `membrowse`

Browse the AtomCtx filesystem layout.

Parameters:

- `uri`: target URI
- `view?`: `list | tree | stat`
- `recursive?`: only for `view: "list"`
- `simple?`: only for `view: "list"`

### `memcommit`

Trigger immediate memory extraction for the current session.

Parameters:

- `session_id?`: optional explicit AtomCtx session ID

Returns background task progress or completion details, including `task_id`, `memories_extracted`, and `archived`.

## Usage Examples

Search and then read:

```typescript
const results = await memsearch({
  query: "user coding preferences",
  target_uri: "ctx://user/memories/",
  mode: "auto"
})

const content = await memread({
  uri: results[0].uri,
  level: "auto"
})
```

Browse first:

```typescript
const tree = await membrowse({
  uri: "ctx://resources/",
  view: "tree"
})
```

Force a mid-session commit:

```typescript
const result = await memcommit({})
```

## Notes for Reviewers

- The plugin is designed to run as a first-level `*.ts` file in the OpenCode plugins directory
- It intentionally keeps runtime config, logs, and session maps outside the repository example
- It uses AtomCtx background commit tasks to avoid repeated timeout/retry loops during long memory extraction

## Troubleshooting

- Plugin not loading: confirm the file exists at `~/.config/opencode/plugins/atom_ctx-memory.ts`
- Service unavailable: confirm `ctx-server` is running and reachable at the configured endpoint
- Authentication failed: check `ATOM_CTX_API_KEY` or `atom_ctx-config.json`
- No memories extracted: check that your AtomCtx server has working `vlm` and `embedding` configuration
