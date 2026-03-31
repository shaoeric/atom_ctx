#!/usr/bin/env bash
# ============================================================================
# AtomCtx CLI Usage Examples
#
# This script demonstrates the AtomCtx CLI commands and options.
# It walks through a typical workflow: health check → add resource → browse →
# search → session management → cleanup.
#
# Prerequisites:
#   1. Configure & start the server:
#      Server reads ctx.conf from (priority high → low):
#        a) $CTX_CONFIG_FILE               # env var, highest priority
#        b) ~/.ctx/ctx.conf                  # default path
#      See ctx.conf.example for template.
#
#      ctx-server                            # default: localhost:1933
#      ctx-server --port 8080                # custom port
#      ctx-server --config /path/to/ctx.conf  # explicit config path
#
#   2. Configure CLI connection (ctx-cli.conf):
#      CLI reads ctx-cli.conf from (priority high → low):
#        a) $CTX_CLI_CONFIG_FILE            # env var, highest priority
#        b) ~/.ctx/ctx-cli.conf               # default path
#
#      Example ctx-cli.conf:
#        {
#          "url": "http://localhost:1933",
#          "api_key": null,
#          "agent_id": null,
#          "output": "table"
#        }
#
#      Fields:
#        url      - Server address (required)
#        api_key  - API key for authentication (null = no auth)
#        agent_id - Agent identifier (null = not set)
#        output   - Default output format: "table" or "json" (default: "table")
#
# Usage:
#   bash client_cli.sh
# ============================================================================

set -euo pipefail


section() { printf '\n\033[1;36m── %s ──\033[0m\n' "$1"; }

# ============================================================================
# Global Options
# ============================================================================
#
#   --output, -o   Output format: table (default) or json
#   --version      Show version and exit
#
# Global options MUST be placed before the subcommand:
#   atom_ctx -o json ls ctx://       ✓
#   atom_ctx ls ctx:// -o json       ✗ (won't work)

printf '\033[1m=== AtomCtx CLI Usage Examples ===\033[0m\n'

atom_ctx --version

# ============================================================================
# 1. Health & Status
# ============================================================================

section "1.1 Health Check"
atom_ctx health                          # table: {"healthy": true}
# atom_ctx -o json health                # json:  {"ok": true, "result": {"healthy": true}}

section "1.2 System Status"
atom_ctx status                          # table: component status with ASCII tables

section "1.3 Observer (per-component)"
atom_ctx observer queue                  # queue processor status
# atom_ctx observer vikingdb             # VikingDB connection status
# atom_ctx observer vlm                  # VLM service status
# atom_ctx observer system               # all components (same as `status`)

# ============================================================================
# 2. Resource Management
# ============================================================================

section "2.1 Add Resource"
# Add from URL (use -o json to capture root_uri for later commands)
ROOT_URI=$(atom_ctx -o json add-resource \
  "https://raw.githubusercontent.com/volcengine/AtomCtx/refs/heads/main/README.md" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['root_uri'])")
echo "  root_uri: $ROOT_URI"

# Other add-resource options:
# atom_ctx add-resource ./file --to ctx://dst  # specify target URI
# atom_ctx add-resource ./file --reason "..."     # attach import reason
# atom_ctx add-resource ./file --wait             # block until processing done
# atom_ctx add-resource ./file --wait --timeout 60

section "2.2 Add Skill"
# atom_ctx add-skill ./my_skill/SKILL.md          # from SKILL.md file
# atom_ctx add-skill ./skill_dir                  # from directory
# atom_ctx add-skill "raw skill content"          # from inline text
# atom_ctx add-skill ./skill --wait --timeout 30

section "2.3 Wait for Processing"
atom_ctx wait                            # block until all queues are idle
# atom_ctx wait --timeout 120            # with timeout (seconds)

# ============================================================================
# 3. File System
# ============================================================================

section "3.1 List Directory"
atom_ctx ls ctx://resources/                   # table: name, size, mode, ...
# atom_ctx ls ctx://resources/ --simple        # simple: paths only
# atom_ctx ls ctx://resources/ --recursive     # recursive listing
# atom_ctx -o json ls ctx://resources/         # json output

section "3.2 Directory Tree"
atom_ctx tree "$ROOT_URI"

section "3.3 File Metadata"
atom_ctx stat "$ROOT_URI"                # table: single-row with all metadata

section "3.4 File Operations"
# atom_ctx mkdir ctx://resources/new_dir
# atom_ctx mv ctx://resources/old ctx://resources/new
# atom_ctx rm ctx://resources/file
# atom_ctx rm ctx://resources/dir --recursive

# ============================================================================
# 4. Content Reading (3 levels of detail)
# ============================================================================

section "4.1 Abstract (L0 - shortest summary)"
atom_ctx abstract "$ROOT_URI"

section "4.2 Overview (L1 - structured overview)"
atom_ctx overview "$ROOT_URI"

section "4.3 Read (L2 - full content)"
# atom_ctx read "$ROOT_URI"              # prints full file content

# ============================================================================
# 5. Search
# ============================================================================

section "5.1 Semantic Search (find)"
atom_ctx find "what is atom_ctx" --limit 3
# atom_ctx find "auth" --uri ctx://resources/docs/  # search within URI
# atom_ctx find "auth" --limit 5 --threshold 0.3       # with score threshold
# atom_ctx -o json find "auth"                         # json output

section "5.2 Pattern Search (grep)"
atom_ctx grep "ctx://" "AtomCtx"
# atom_ctx grep "ctx://resources/" "pattern" --ignore-case

section "5.3 File Glob"
atom_ctx glob "**/*.md"
# atom_ctx glob "*.py" --uri ctx://resources/src/   # search within URI

# ============================================================================
# 6. Relations
# ============================================================================

section "6.1 List Relations"
atom_ctx relations "$ROOT_URI"

section "6.2 Link / Unlink"
# atom_ctx link ctx://a ctx://b ctx://c --reason "related docs"
# atom_ctx unlink ctx://a ctx://b

# ============================================================================
# 7. Session Management
# ============================================================================

section "7.1 Create Session"
SESSION_ID=$(atom_ctx -o json session new | python3 -c "
import sys, json; print(json.load(sys.stdin)['result']['session_id'])
")
echo "  session_id: $SESSION_ID"

section "7.2 Add Messages"
atom_ctx session add-message "$SESSION_ID" \
  --role user --content "Tell me about AtomCtx"
atom_ctx session add-message "$SESSION_ID" \
  --role assistant --content "AtomCtx is an agent-native context database."

section "7.3 Get Session Details"
atom_ctx session get "$SESSION_ID"

section "7.4 Context-Aware Search"
# search uses session history for better relevance
atom_ctx search "how to use it" --session-id "$SESSION_ID" --limit 3
# atom_ctx search "query" --session-id "$SESSION_ID" --threshold 0.3

section "7.5 List All Sessions"
atom_ctx session list

section "7.6 Commit Session (archive + extract memories)"
# atom_ctx session commit "$SESSION_ID"

section "7.7 Delete Session"
atom_ctx session delete "$SESSION_ID"

# ============================================================================
# 8. Import / Export
# ============================================================================

section "8.1 Export"
# atom_ctx export ctx://resources/docs ./docs.ctxpack

section "8.2 Import"
# atom_ctx import ./docs.ctxpack ctx://resources/imported
# atom_ctx import ./docs.ctxpack ctx://resources/imported --force
# atom_ctx import ./docs.ctxpack ctx://resources/imported --no-vectorize

# ============================================================================
# Output Format Comparison
# ============================================================================

section "Output: table (default)"
atom_ctx ls ctx://resources/

section "Output: json"
atom_ctx -o json ls ctx://resources/

section "Output: -o json (for scripts)"
atom_ctx -o json ls ctx://resources/

printf '\n\033[1m=== Done ===\033[0m\n'
