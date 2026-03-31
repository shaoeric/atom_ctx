import { exec } from "child_process"
import { promisify } from "util"
import { readFileSync, mkdirSync, writeFileSync, existsSync } from "fs"
import { homedir } from "os"
import { join, dirname } from "path"
import { fileURLToPath } from "url"

const execAsync = promisify(exec)
const __dirname = dirname(fileURLToPath(import.meta.url))

// ── Helpers ───────────────────────────────────────────────────────────────────

async function run(cmd, opts = {}) {
  return execAsync(cmd, { timeout: 10000, ...opts })
}

async function isHealthy() {
  try {
    await run("ctx health", { timeout: 3000 })
    return true
  } catch {
    return false
  }
}

async function startServer() {
  // Start in background, wait up to 30s for healthy
  await run("ctx-server > /tmp/ctx-server.log 2>&1 &")
  for (let i = 0; i < 10; i++) {
    await new Promise((r) => setTimeout(r, 3000))
    if (await isHealthy()) return true
  }
  return false
}

let initPromise = null

function makeToast(client) {
  return (message, variant = "warning") =>
    client.tui.showToast({
      body: { title: "AtomCtx", message, variant, duration: 8000 },
    }).catch(() => {})
}

// ── Skill auto-install ────────────────────────────────────────────────────────

function installSkill() {
  const src = join(__dirname, "skills", "atom_ctx", "SKILL.md")
  const dest = join(homedir(), ".config", "opencode", "skills", "atom_ctx", "SKILL.md")
  mkdirSync(dirname(dest), { recursive: true })
  const content = readFileSync(src, "utf8")
  if (!existsSync(dest) || readFileSync(dest, "utf8") !== content) {
    writeFileSync(dest, content, "utf8")
  }
}

// ── Repo context cache ────────────────────────────────────────────────────────

let cachedRepos = null
let lastFetchTime = 0
const CACHE_TTL_MS = 60 * 1000

async function loadRepos() {
  const now = Date.now()
  if (cachedRepos !== null && now - lastFetchTime < CACHE_TTL_MS) return

  try {
    const { stdout } = await run(
      "ctx --output json ls ctx://resources/ --abs-limit 2000"
    )
    const items = JSON.parse(stdout)?.result ?? []
    const repos = items
      .filter((item) => item.uri?.startsWith("ctx://resources/"))
      .map((item) => {
        const name = item.uri.replace("ctx://resources/", "").replace(/\/$/, "")
        return item.abstract
          ? `- **${name}** (${item.uri})\n  ${item.abstract}`
          : `- **${name}** (${item.uri})`
      })
    if (repos.length > 0) {
      cachedRepos = repos.join("\n")
      lastFetchTime = now
    }
  } catch {}
}

// ── Init: check deps, start server if needed ─────────────────────────────────

async function _init(client) {
  const toast = makeToast(client)

  // server already running
  if (await isHealthy()) return true

  // check if ctx is installed
  try {
    await run("command -v ctx", { timeout: 2000 })
  } catch {
    await toast("atom_ctx is not installed. Run: pip install atom_ctx", "error")
    return false
  }

  // installed but no config file — cannot start
  const ctxConf = join(homedir(), ".ctx", "ctx.conf")
  if (!existsSync(ctxConf)) {
    await toast("~/.ctx/ctx.conf not found. Please configure API keys before starting the server.", "warning")
    return false
  }

  // installed + config exists — auto-start silently
  const started = await startServer()
  if (!started) {
    await toast("Failed to start atom_ctx server. Check logs: /tmp/ctx-server.log", "error")
    return false
  }

  return true
}

async function init(client) {
  if (!initPromise) initPromise = _init(client).finally(() => { initPromise = null })
  return initPromise
}

// ── Plugin export ─────────────────────────────────────────────────────────────

/**
 * @type {import('@opencode-ai/plugin').Plugin}
 */
export async function AtomCtxPlugin({ client }) {
  const toast = makeToast(client)

  try {
    installSkill()
  } catch (e) {
    await toast(`Failed to install skill: ${e.message}`, "error")
  }

  // init in background — do not block opencode startup
  Promise.resolve().then(async () => {
    const ready = await init(client)
    if (ready) await loadRepos()
  })

  return {
    "experimental.chat.system.transform": (_input, output) => {
      if (!cachedRepos) return
      output.system.push(
        `## AtomCtx — Indexed Code Repositories\n\n` +
        `The following repos are semantically indexed and searchable.\n` +
        `When the user asks about any of these projects or their internals, ` +
        `you MUST proactively load skill("atom_ctx") and use the correct ctx commands to search and retrieve content before answering.\n\n` +
        cachedRepos
      )
    },

    "session.created": async () => {
      const ready = await init(client)
      if (ready) {
        cachedRepos = null
        await loadRepos()
      }
    },
  }
}
