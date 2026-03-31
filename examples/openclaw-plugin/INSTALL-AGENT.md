# AtomCtx Memory Plugin — Agent Install Guide

> For AI Agents (Claude Code, Cursor, etc.) to follow step-by-step.
> Principle: auto-detect what you can; only ask the user when detection fails.

---

## Step 0: Choose Target OpenClaw Instance

Check if the user has multiple OpenClaw instances:

```bash
ls -d ~/.openclaw* 2>/dev/null
```

If multiple directories exist (e.g. `~/.openclaw`, `~/.openclaw-openclaw-second`), ask the user which instance to install to. Pass the chosen directory via `--workdir`:

```bash
npx ./examples/openclaw-plugin/setup-helper --workdir ~/.openclaw-openclaw-second
```

If only `~/.openclaw` exists, proceed with the default.

## Step 1: Choose Deployment Mode

Ask the user: "How do you want to use AtomCtx?"

- **A) Local** — Run AtomCtx on this machine (requires Python >= 3.10)
- **B) Remote** — Connect to an existing AtomCtx server (only needs the server URL and API Key)

→ A: Go to [Local Deployment Path](#local-deployment-path)
→ B: Go to [Remote Connection Path](#remote-connection-path)

---

## Local Deployment Path

### Step L1: Check Environment

Run each check. Every check must pass before continuing.

**1. Python**

```bash
python3 --version
```

- Pass: >= 3.10
- Fail: Tell user "Python >= 3.10 is required. Install from https://www.python.org/downloads/"
- Multiple versions: Ask user which Python path to use

**2. Node.js**

```bash
node -v
```

- Pass: >= v22
- Fail: Tell user "Node.js >= 22 is required. Install from https://nodejs.org/"

**3. OpenClaw**

```bash
openclaw --version
```

- Pass: Version output present
- Fail: Tell user to run `npm install -g openclaw && openclaw onboard`

### Step L2: Install AtomCtx

```bash
python3 -m pip install atom-ctx --upgrade
```

- Pass: Continue
- Fail with `externally-managed`:
  ```bash
  python3 -m venv ~/.ctx/venv
  ~/.ctx/venv/bin/pip install atom-ctx --upgrade
  ```
  Set `ATOM_CTX_PYTHON=~/.ctx/venv/bin/python` for later steps
- Fail with `No matching distribution`: Python is below 3.10, tell user to upgrade
- Other failure: Print full error, ask user

Verify:

```bash
python3 -c "import atom_ctx; print('ok')"
```

### Step L3: Configure

Check if `~/.ctx/ctx.conf` already exists:

- **Exists**: Ask user "Found existing config at ~/.ctx/ctx.conf. Keep it?"
  - Yes: Skip to Step L4
  - No: Continue with configuration below

- **Does not exist**: Collect configuration

**Ask user for API Key:**

> "Please provide your Volcengine Ark API Key (used for Embedding and VLM model calls).
> Get one at https://console.volcengine.com/ark if you don't have one."

Run the setup helper:

```bash
npm install -g openclaw-atom_ctx-setup-helper
ov-install
```

At the interactive prompts:
- Workspace: Press Enter for default path
- API Key: Enter the user's key
- VLM model: Press Enter for default `doubao-seed-2-0-pro-260215`
- Embedding model: Press Enter for default `doubao-embedding-vision-251215`
- Ports: Press Enter for default 1933/1833

Wait for `Setup complete!`

### Step L4: Start and Verify

```bash
source ~/.openclaw/atom_ctx.env && openclaw gateway
```

- Pass: Output contains `atom_ctx: local server started`
- Fail with `port occupied`:
  The port is used by another process. Change port:
  ```bash
  openclaw config set plugins.entries.ctx.config.port 1934
  source ~/.openclaw/atom_ctx.env && openclaw gateway
  ```
- Fail with `subprocess exited`: Check stderr for Python errors — usually wrong API Key or atom_ctx not installed properly

Verify:

```bash
openclaw status
```

ContextEngine line should show `enabled (plugin atom_ctx)`.

Tell user: "AtomCtx memory is active. I'll automatically remember important facts from our conversations and recall them when relevant."

---

## Remote Connection Path

### Step R1: Collect Connection Info

Ask user for:

1. **AtomCtx server URL** (e.g. `http://10.0.0.1:1933`)
   > This is the AtomCtx HTTP API address.

2. **AtomCtx API Key** (optional)
   > Required if the server has `root_api_key` configured. This authenticates to the AtomCtx server — it is NOT a Volcengine Ark API Key.

### Step R2: Check Environment

**1. Node.js**

```bash
node -v
```

- Pass: >= v22
- Fail: Tell user to install Node.js >= 22

**2. OpenClaw**

```bash
openclaw --version
```

- Pass: Version output present
- Fail: `npm install -g openclaw && openclaw onboard`

> Remote mode does **not** require Python — AtomCtx runs on the remote server.

### Step R3: Install Plugin and Configure

```bash
npm install -g openclaw-atom_ctx-setup-helper
ov-install
# Select remote mode, enter AtomCtx server URL and API Key
```

Alternatively, configure manually (substitute user-provided values). If targeting a non-default instance, prefix each command with `OPENCLAW_STATE_DIR=<workdir>`:

```bash
openclaw config set plugins.enabled true --json
openclaw config set plugins.slots.contextEngine atom_ctx
openclaw config set plugins.entries.ctx.config.mode remote
openclaw config set plugins.entries.ctx.config.baseUrl "<user's server URL>"
openclaw config set plugins.entries.ctx.config.apiKey "<user's API Key>"
openclaw config set plugins.entries.ctx.config.autoRecall true --json
openclaw config set plugins.entries.ctx.config.autoCapture true --json
```

If user has no API Key (server auth not enabled), skip the apiKey line.

### Step R4: Start and Verify

```bash
openclaw gateway
```

- Pass: Output contains `atom_ctx: initialized`
- Fail with connection error: Verify server is reachable — `curl <baseUrl>/health` should return `{"status":"ok"}`

```bash
openclaw status
```

ContextEngine line should show `enabled (plugin atom_ctx)`.

Tell user: "AtomCtx memory is connected to the remote server. I'll automatically remember important facts and recall them when relevant."

---

## Field Reference

| Field | Meaning | Required For |
|-------|---------|-------------|
| Volcengine Ark API Key | Embedding + VLM model access | Local |
| AtomCtx API Key | Server authentication key | Remote (if server has auth enabled) |
| agentId | Identifies this agent to AtomCtx | Both (auto-generated if not set) |
| baseUrl | AtomCtx HTTP address | Remote |
| workspace | Data storage directory | Local |
| server port | AtomCtx HTTP port (default 1933) | Local |
| VLM model | Memory extraction model | Local |
| Embedding model | Text vectorization model | Local |

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `port occupied` | Port used by another process | Change port in config, e.g. `openclaw config set plugins.entries.ctx.config.port 1934` |
| `extracted 0 memories` | Wrong API Key or model name | Check `api_key` and `model` in `~/.ctx/ctx.conf` |
| `externally-managed-environment` | Python PEP 668 restriction | Install via venv |
| `ECONNREFUSED` | Remote server unreachable | Verify baseUrl and network connectivity |
| Plugin not loaded | Env file not sourced | `source ~/.openclaw/atom_ctx.env` (local mode) |
