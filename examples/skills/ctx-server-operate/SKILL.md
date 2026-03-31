---
name: ov-server-operate
description: Operate and maintain AtomCtx server - configure, install, start, stop, and cleanup the server. Use when need to setup or manage AtomCtx service deployment.
compatibility: AtomCtx CLI configured at `~/.ctx/ctx-cli.conf`
---

# AtomCtx Server Operations

This guide provides standard operating procedures for deploying, managing, and maintaining AtomCtx servers in production environments.

## Table of Content
- Service Configuration
- Environment Setup with uv
- Server Startup with nohup
- Server Shutdown
- Data Cleanup Procedure
- Verification and Troubleshooting

## Service Configuration

### Default Paths and Structure

AtomCtx uses the following standard directory structure under `~/.ctx/`:

```
~/.ctx/
├── ctx.conf             # Server configuration (required)
├── ctx-cli.conf          # CLI client configuration
├── ov-venv/            # Virtual environment (created by uv)
├── log/                # Server log directory
│   ├── ctx-server.log   # server stdout log
│   └── ctx-server.log          # server log
└── data/               # Workspace data (configured in ctx.conf)
    ├── ...
    └── ...
```

### Configuration Files

#### 1. Server Config (`~/.ctx/ctx.conf`)

Create the configuration file with at minimum the following configuration.
Note 1: Replace the api-key with your own api-key. If you don't have one, ask the user to get one (follow the Volcengine Ark platform guide).
Note 2: Replace the root_api_key with your own root-api-key. Ask the user to set one — it will be used for authentication when the CLI connects to the server.

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 1933,
    "root_api_key": "your-root-api-key"
  },
  "storage": {
    "workspace": "~/.ctx/data/"
  },
  "parsers": {
    "code": {
      "gitlab_domains": ["code.byted.org"]
    }
  },
  "embedding": {
    "dense": {
        "model": "doubao-embedding-vision-250615",
        "api_key": "your-volcengine-api-key",
        "api_base": "https://ark.cn-beijing.volces.com/api/v3",
        "dimension": 1024,
        "input": "multimodal",
        "provider": "volcengine"
    }
  },
  "vlm": {
    "model": "doubao-seed-1-8-251228",
    "api_key": "your-volcengine-api-key",
    "api_base": "https://ark.cn-beijing.volces.com/api/v3",
    "temperature": 0.0,
    "max_retries": 2,
    "provider": "volcengine",
    "thinking": false
  },
  "log": {
    "level": "INFO",
    "output": "file",
    "rotation": true,
    "rotation_days": 3,
    "rotation_interval": "midnight"
  }
}
```

#### 2. CLI Config (`~/.ctx/ctx-cli.conf`)

For client connections from localhost:

```json
{
  "url": "http://localhost:1933",
  "api_key": "your-root-api-key"
}
```

For remote connections, set the url to the remote server address (for example, the server EIP).

## Environment Setup with uv

### Step 1: Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### Step 2: Create Virtual Environment

Create a dedicated virtual environment at `~/.ctx/ov-venv`:

```bash
# Create venv with Python 3.10+
cd ~/.ctx
uv venv --python 3.12 ov-venv
```

### Step 3: Activate and Install AtomCtx

```bash
# Activate the virtual environment
source ~/.ctx/ov-venv/bin/activate

# Install or upgrade to latest atom_ctx
uv pip install --upgrade atom_ctx --force-reinstall

# Verify installation
which ctx-server
ctx-server --version
ctx-server --help
```

### Step 4: Create Log Directory

```bash
mkdir -p ~/.ctx/log
```

## Server Startup with nohup

### Standard Startup Procedure

```bash
# 1. Activate the virtual environment
source ~/.ctx/ov-venv/bin/activate

# 2. Ensure log directory exists
mkdir -p ~/.ctx/log

# 3. Start server with nohup
nohup ctx-server \
    > ~/.ctx/log/ctx-server.log 2>&1 &

# 4. Save PID for later reference
echo $! > ~/.ctx/server.pid

# 5. Verify startup after 10 secs
sleep 10
curl -s http://localhost:1933/health
```

### Verify Server is Running

```bash
# Method 1: Check health endpoint
curl http://localhost:1933/health
# Expected: {"status": "ok"}

# Method 2: Check readiness (includes storage checks)
curl http://localhost:1933/ready

# Method 3: Check process
ps aux | grep ctx-server | grep -v grep

# Method 4: Check log output
tail -10 ~/.ctx/log/ctx-server.log
tail -50 ~/.ctx/log/ctx-server.log
```

## Server Shutdown

### Graceful Shutdown Procedure

```bash
# 1. Find the server process
ps aux | grep ctx-server | grep -v grep

# 2. Send SIGTERM for graceful shutdown
# Option A: Using saved PID
if [ -f ~/.ctx/server.pid ]; then
    kill $(cat ~/.ctx/server.pid)
    rm ~/.ctx/server.pid
fi

# Option B: Using pgrep
pkill -f ctx-server

# 3. Wait for process to stop
sleep 3

# 4. Verify it stopped
ps aux | grep ctx-server | grep -v grep || echo "Server stopped successfully"

# 5. If still running, force kill
if pgrep -f ctx-server > /dev/null; then
    echo "Force killing server..."
    pkill -9 -f ctx-server
fi
```

## Data Cleanup Procedure

### When to Use This Procedure

Perform full data cleanup in these scenarios:
1. Version upgrade with incompatible data format
2. Corrupted or inconsistent data
3. Need to reset to fresh state
4. Storage space reclamation

### Standard Cleanup Workflow

**CRITICAL: ALWAYS BACKUP BEFORE DELETING DATA**

```bash
# ==========================================
# STEP 1: STOP THE SERVER FIRST
# ==========================================
echo "Step 1: Stopping AtomCtx Server..."
if pgrep -f ctx-server > /dev/null; then
    pkill -f ctx-server
    sleep 3
    if pgrep -f ctx-server > /dev/null; then
        pkill -9 -f ctx-server
        sleep 1
    fi
fi

# Verify server is stopped
if pgrep -f ctx-server > /dev/null; then
    echo "ERROR: Server still running! Cannot proceed."
    exit 1
fi
echo "✓ Server stopped"

# ==========================================
# STEP 2: CREATE BACKUP (REQUIRED)
# ==========================================
echo ""
echo "Step 2: Creating backup..."
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/.ctx/backup_${BACKUP_DATE}

mkdir -p ${BACKUP_DIR}

# Backup config files
cp ~/.ctx/ctx.conf ${BACKUP_DIR}/ 2>/dev/null || true
cp ~/.ctx/ctx-cli.conf ${BACKUP_DIR}/ 2>/dev/null || true

# Backup workspace (if exists)
WORKSPACE=$(python3 -c '
import json
import os
config_path = os.path.expanduser("~/.ctx/ctx.conf")
if os.path.exists(config_path):
    with open(config_path) as f:
        cfg = json.load(f)
        ws = cfg.get("storage", {}).get("workspace", "./data")
        print(os.path.expanduser(ws))
' 2>/dev/null || echo "~/.ctx/data")

if [ -d "${WORKSPACE}" ]; then
    echo "Backing up workspace: ${WORKSPACE}"
    tar -czf ${BACKUP_DIR}/workspace_backup.tar.gz -C $(dirname ${WORKSPACE}) $(basename ${WORKSPACE})
fi

# Backup log
if [ -d ~/.ctx/log ]; then
    cp -r ~/.ctx/log ${BACKUP_DIR}/ 2>/dev/null || true
fi

echo "✓ Backup created at: ${BACKUP_DIR}"
ls -lh ${BACKUP_DIR}/

# ==========================================
# STEP 3: CONFIRM DELETION
# ==========================================
echo ""
echo "=========================================="
echo "WARNING: ABOUT TO DELETE ALL DATA!"
echo "=========================================="
echo "Workspace to delete: ${WORKSPACE}"
echo "Backup location: ${BACKUP_DIR}"
echo ""
read -p "Type 'DELETE' to confirm data removal: " CONFIRM

if [ "${CONFIRM}" != "DELETE" ]; then
    echo "Cleanup cancelled. Backup preserved at ${BACKUP_DIR}"
    exit 0
fi

# ==========================================
# STEP 4: DELETE DATA
# ==========================================
echo ""
echo "Step 4: Deleting data..."

# Delete workspace
if [ -d "${WORKSPACE}" ]; then
    echo "Deleting workspace: ${WORKSPACE}"
    rm -rf "${WORKSPACE}"
fi

# Optional: Delete old log (uncomment if needed)
# echo "Deleting old log..."
# rm -rf ~/.ctx/log/*

# Cleanup any temporary files
rm -f ~/.ctx/server.pid

echo "✓ Data deleted successfully"

# ==========================================
# STEP 5: COMPLETION
# ==========================================
echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo "Backup preserved at: ${BACKUP_DIR}"
echo ""
echo "Next steps:"
echo "1. Reconfigure ctx.conf if needed"
echo "2. Start the server: ctx-server"
echo "3. Verify with: curl http://localhost:1933/health"
echo ""
echo "To restore from backup:"
echo "  tar -xzf ${BACKUP_DIR}/workspace_backup.tar.gz -C $(dirname ${WORKSPACE})"
```

### Quick Cleanup (for Development Only)

```bash
# WARNING: Only use in development!
# No backup created - data loss guaranteed!

# 1. Stop server
pkill -f ctx-server
sleep 2
pkill -9 -f ctx-server 2>/dev/null || true

# 2. Delete workspace (adjust path as needed)
rm -rf ~/.ctx/data

# 3. Cleanup PID and temp files
rm -f ~/.ctx/server.pid

echo "Quick cleanup complete"
```

## Verification and Troubleshooting

### Health Check Verification

```bash
# Basic health check (always available)
curl http://localhost:1933/health
# Expected: {"status": "ok"}

# Readiness check (verifies all components)
curl http://localhost:1933/ready
# Expected: {"status": "ready", "checks": {"agfs": "ok", "vectordb": "ok", "api_key_manager": "ok"}}

# System status via CLI (~/.ctx/ctx-cli.conf should be configured)
ctx status
```

### Common Issues and Solutions

#### Issue: Server won't start

**Check:**
```bash
# 1. Check if port is in use
lsof -i :1933
netstat -tulpn | grep 1933

# 2. Check log for errors
tail -10 ~/.ctx/log/ctx-server.log
tail -100 ~/.ctx/log/ctx-server.log


# 3. Verify config file is valid JSON
python3 -c 'import json, os; json.load(open(os.path.expanduser("~/.ctx/ctx.conf"))); print("Config is valid")'

# 4. Verify virtual environment
source ~/.ctx/ov-venv/bin/activate
which ctx-server
pip list | grep atom_ctx
```

**Solution:**
```bash
# If port conflict: kill the process or use different port
lsof -ti :1933 | xargs kill -9 2>/dev/null || true

# Or start on different port
nohup ctx-server --port 1934 > ~/.ctx/log/ctx-server.log 2>&1 &
```

#### Issue: API Key Errors

**Check:**
```bash
# Verify API keys in config
python3 -c '
import json, os
cfg = json.load(open(os.path.expanduser("~/.ctx/ctx.conf")))
print("Embedding provider:", cfg.get("embedding", {}).get("dense", {}).get("provider"))
print("VLM provider:", cfg.get("vlm", {}).get("provider"))
print("API keys set:", bool(cfg.get("embedding", {}).get("dense", {}).get("api_key")), bool(cfg.get("vlm", {}).get("api_key")))
'
```

**Solution:** Verify API keys are correct and have the required permissions. Check network connectivity to the model provider endpoints. Ensure API keys are not expired.

## Prerequisites

- Python 3.10+ installed
- uv package manager available
- Sufficient disk space for workspace and log
- API keys for embedding and VLM models configured
- Network access to model providers (if using cloud models)
