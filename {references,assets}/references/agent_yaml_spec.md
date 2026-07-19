# `agent.yaml` — field-by-field

`agent.yaml` is the root manifest Agent Studio reads to render the agent's config page and launch the runtime. The docs don't publish an exhaustive schema (Beta product, May 2026), so what follows is reconstructed from the visible config surface — every section on the agent configuration page maps to one of these keys.

When in doubt, let Agent Studio write the file (via the UI) and read it back. Hand-editing is fine for tweaks once the file exists.

## Skeleton

```yaml
name: my-agent
description: One-sentence what-this-agent-is-for

ai_provider:
  provider: anaconda            # anaconda | anaconda-desktop | anthropic | openai | google | groq | custom
  model: claude-sonnet-4-6
  temperature: 0.7              # 0.0 (deterministic) ... 2.0 (creative)
  max_tokens: null              # null = provider default
  output_format: text           # text | json

sandbox:
  enabled: true
  network: outbound             # outbound | isolated | host
  cpus: 2                       # optional cap
  memory_gb: 4                  # optional cap
  mounts:
    - host_path: /Users/apollo/data
      sandbox_path: /work/data
      mode: ro                  # ro | rw

knowledge:
  system_prompt: |
    You are <agent name>. Your role is to ...
    When to use which tool: ...
  documents:
    - documents/glossary.md
    - documents/style-guide.md

capabilities:
  python_tools:
    - tools/main.py
    - tools/data_ops.py
  mcp_servers:
    - name: github
      ref: catalog              # registered in the global Add-ons → MCP catalog
      approvals:
        github_create_issue: ask
        github_list_repos: allow
    - name: local_postgres
      ref: tools/mcp.json#local_postgres
      approvals:
        query: allow
  skills:
    - skills/atp
    - skills/code-review
  plugins:
    - atlassian
```

## Field notes

### `name` and `description`

What the user sees on the Agents page card. Keep `description` to one line — it's the tooltip-length blurb. Longer rationale goes in the system prompt.

### `ai_provider`

`provider` must match exactly one of the providers visible in **AI Providers**. Defaults to `anaconda` (hosted; Claude Sonnet 4.6) when omitted. For local-only runs, `anaconda-desktop` requires a model server running in Anaconda Desktop.

`temperature` — keep it 0.0–0.3 for analytical/factual agents, 0.7 for general assistants, 1.0+ only when the user explicitly wants creative output.

`max_tokens: null` is almost always right. Set a cap only if responses are blowing past what a downstream pipeline expects.

`output_format: json` is only useful when the agent's _entire_ output needs to be valid JSON and downstream code parses it. Don't pair this with conversational agents — it breaks chat UX.

### `sandbox`

Defaults are sensible: `enabled: true`, `network: outbound`. Override deliberately:

- `network: isolated` for offline/airgapped agents (no external API calls, no MCP servers reachable outside the container).
- `network: host` only when the agent must bind to a host port. Avoid otherwise — it gives up isolation.
- `mounts` — be explicit and prefer `ro`. Every mount is an attack surface and a privacy surface.

### `knowledge.system_prompt`

This is the single highest-leverage field in the file. It sets the agent's role, voice, and (critically) _when to use which tool_. Two things to put in here that often get forgotten:

1. **A "tool decision table"** — a short list of "if user asks X, prefer tool Y." Without this the agent often defaults to summarizing rather than acting.
2. **A "what NOT to do" line** — explicit refusals for the failure modes you've already seen.

### `knowledge.documents`

Relative paths into `documents/`. Inserted into the context window at the start of every conversation. Budget them carefully — every kilobyte costs latency and money on every turn.

### `capabilities.python_tools`

List of `.py` files in `tools/`. Each `@tool` function inside becomes available. Agent Studio handles tool approval (`allow` / `ask` / `disabled`) through the UI — that state is stored separately, not in this file (the file just declares the modules exist).

### `capabilities.mcp_servers`

Two kinds of references:

- `ref: catalog` with `name: <server-name>` — points at a server in the desktop-wide catalog (Add-ons → MCP).
- `ref: tools/mcp.json#<key>` — points at a server defined locally in this project's `tools/mcp.json`.

`approvals` is per-tool: `allow` (no prompt), `ask` (prompt user), `disabled` (agent cannot use). Default to `ask` for anything destructive (`*_create_*`, `*_delete_*`, `*_send_*`, `*_publish_*`).

### `capabilities.skills`

List of paths to skill folders (each containing a `SKILL.md`). Can be:

- Local: `skills/<name>` for bundled skills.
- Global: `catalog:<name>` for skills in the desktop-wide Add-ons → Skills catalog.

### `capabilities.plugins`

Plugins bundle MCP servers + skills together. As of May 2026 the published plugins are: `atlassian`, `miro`, `nteract`, `omni`. Listing one here adds all its tools and skills in a single step.

## A common-case minimal example

For a "data CSV cleaner" agent the user just wants to start with:

```yaml
name: csv-cleaner
description: Cleans and normalizes messy CSV files.

ai_provider:
  provider: anaconda
  model: claude-sonnet-4-6
  temperature: 0.2

sandbox:
  enabled: true
  network: isolated
  mounts:
    - host_path: ~/Downloads
      sandbox_path: /work/input
      mode: ro
    - host_path: ~/Documents/cleaned-csvs
      sandbox_path: /work/output
      mode: rw

knowledge:
  system_prompt: |
    You clean CSV files. You read from /work/input and write to /work/output.
    Always preserve the original header row in your output.
    When the user is ambiguous about the cleaning rules, ASK rather than guess.

capabilities:
  python_tools:
    - tools/csv_io.py
```

That's a complete, runnable agent. Tools live in `tools/csv_io.py`, no skills, no external MCP, isolated network. Use that as the "good defaults" shape when the user hasn't given enough info to do more.

## What this file does NOT contain

- Approval state (`allow`/`ask`/`disabled` on individual Python tools) — Agent Studio stores this separately.
- API keys — those go through AI Providers (UI), not `agent.yaml`.
- Conversation history — stored by Agent Studio per session, never in this file.
- Pixi dependencies — those live in `pixi.toml`.

When you find yourself wanting to put any of the above into `agent.yaml`, stop and reconsider.
