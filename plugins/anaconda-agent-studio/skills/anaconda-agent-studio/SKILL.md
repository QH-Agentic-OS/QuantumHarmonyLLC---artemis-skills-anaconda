---
name: anaconda-agent-studio
description: Scaffold, configure, and ship agents for Anaconda Agent Studio (the Beta desktop app for local AI agents). Use this whenever the user mentions Anaconda Agent Studio, `agent.yaml`, `pixi.toml`, `anaconda_agent_runtime`, `@tool` decorators with that runtime, an Agent Studio plugin, tool servers, or wants to "build an agent in Anaconda" / "register an MCP server in Agent Studio" / "make my Claude skill work in Anaconda." Also use when the user wants to migrate an existing Claude skill, ATP agent, or MCP server into the Agent Studio catalog, or set up multi-agent orchestration where each agent is exposed as an MCP server on localhost.
---

# Anaconda Agent Studio

## What this skill is for

Anaconda Agent Studio is a desktop app (Beta as of May 2026) that builds, runs, and orchestrates local AI agents. Each agent is a folder on disk with a stable, well-defined layout. Each running agent exposes itself as an MCP server on localhost, so agents can call other agents the same way they call any other MCP tool.

The single most important practical fact: **Agent Studio's skill catalog uses the same SKILL.md format (YAML frontmatter + Markdown body) that Claude does.** A skill authored well for one drops into the other unchanged. Hold onto that — it shapes most decisions in this guide.

This skill helps you do four things:

1. Scaffold a new Agent Studio agent project from scratch with the right file layout.
2. Author the moving parts — `agent.yaml`, `pixi.toml`, Python `@tool` modules, `mcp.json`, and skills.
3. Register existing pieces (an MCP server, a Claude skill, an ATP agent) into Agent Studio's catalog.
4. Wire multi-agent setups where agents call each other over MCP (SSE).

## When to load which reference

Don't read everything. Load only what the current task needs:

| Task | Reference to read |
|---|---|
| Building a new agent from scratch (file layout) | `references/project_structure.md` then `references/agent_yaml_spec.md` |
| Actually building & running it — the commands, env resolve, verifying it loaded | `references/build_and_run.md` |
| Anything failing — an error, "it won't load," a cryptic app message | `references/troubleshooting.md` |
| Adding Python tools / writing `@tool` functions / configuring `mcp.json` | `references/tool_authoring.md` |
| Migrating or writing a SKILL.md for the catalog | `references/skills_in_anaconda.md` |
| Connecting agents to each other, or to Claude Desktop / Cursor / VS Code | `references/orchestration.md` |
| Anything ATP-related (Artemis personas, validators, ATP headers) | `references/atp_bridge.md` |

A bundled script does the deterministic preflight check:
- `scripts/validate_agent.py <project-dir>` — parses `agent.yaml`, `pixi.toml`, and `tools/mcp.json` against the documented schema and reports problems (bad provider name, `localhost` URL that won't resolve from the sandbox, missing tool path, dangling `mcp.json` reference) *before* Agent Studio fails on them with a one-line error. Run it as the last build step and after any hand-edit; `--strict` treats warnings as failures for a CI gate.

Templates ready to copy live in `assets/`:
- `agent_yaml_template.yaml` — starter agent.yaml with all the configurable rows
- `pixi_toml_template.toml` — pixi project file with `anaconda_agent_runtime`
- `tool_module_template.py` — a Python tool module with proper `@tool` decoration
- `mcp_json_template.json` — MCP server registration for the agent
- `skill_md_template.md` — SKILL.md authored for both Claude and Agent Studio

## The agent project layout

Every Agent Studio agent is a directory shaped like this:

```
my-agent/
├── agent.yaml              # The agent definition: provider, model, system prompt, capabilities
├── pixi.toml               # Pixi project file (Anaconda's package manager); includes anaconda_agent_runtime
├── documents/              # Reference files inserted into context at conversation start
├── packages/               # Bundled Python wheels (anaconda_agent_runtime-*.whl etc.)
├── skills/                 # Skill catalog folders — each contains a SKILL.md
│   └── github-cli/
│       └── SKILL.md
├── tools/                  # Python @tool modules + mcp.json
│   ├── __init__.py
│   ├── csv_io.py
│   └── mcp.json
└── tree.md                 # Optional human-readable map of the project
```

Two folders deserve emphasis because they're where most of the work happens:

- **`tools/`** — Each `.py` file is a *module*. Inside a module, every function decorated with `@tool` from `anaconda_agent_runtime.tools` becomes a callable tool. Argument type hints define the input schema; the docstring becomes the tool description. `mcp.json` in this folder registers external MCP servers the agent should call out to.
- **`skills/`** — Each subfolder is a skill. The required file is `SKILL.md`. Skills tell the agent *when and how* to use its tools — they're the workflow layer above the raw tool primitives.

## Build, validate, run — at a glance

Agent Studio is the *run* surface (you load a project folder into the app), and `pixi` is the *environment*. The reliable loop is: **scaffold → resolve the env with pixi → preflight-validate → load → smoke-test → verify it loaded.** Resolving and validating from the terminal first turns the app's one-line failures into readable errors.

```bash
mkdir -p my-agent/{tools,skills,documents,packages} && cd my-agent
# copy assets/ templates, fill agent.yaml, write tools/*.py, : > tools/__init__.py
pixi install && pixi run python -c "import anaconda_agent_runtime; print('OK')"
python /path/to/skill/scripts/validate_agent.py . --strict
# Agent Studio → Agents → Open → drag folder → confirm tools + provider resolve → smoke-test a tool call
```

The full step-by-step (with the prerequisite checklist and the "verify it loaded" checks) is in `references/build_and_run.md`. When any step's check fails, stop there — `references/troubleshooting.md` is organized by exactly these layers (app launch, macOS signing/keychain, pixi solve, Docker/sandbox, agent.yaml, MCP/SSE, skills).

## The five capability types

When configuring an agent, four things plug into the "Capabilities" slot (the docs list these explicitly, plus Plugins as a bundling layer):

1. **Python Tool** — local `@tool` functions. Use when the work is mostly computation, file munging, or calling a service the agent should "own."
2. **Plugin** — a pre-built bundle of MCP servers + skills shipped by Anaconda (Atlassian, Miro, nteract, Omni). Use when one exists for the target service; don't recreate.
3. **MCP Server** — external service over stdio or SSE. Use for anything not covered by a plugin and not appropriate as a local Python tool.
4. **Skill** — workflow Markdown. Use when the agent needs procedural guidance for how to chain its tools together, not a new tool.

A useful mental model: **Python Tools and MCP Servers are *verbs* (what the agent can do). Skills are *recipes* (how to combine the verbs to accomplish something). Plugins are pre-bagged grocery kits of both.**

## Sandbox: the default, and what to set

Sandbox runs the agent in a Docker container. Defaults are sensible — outbound network on, no filesystem access unless you mount it. Three things to remember:

- **Docker Desktop must be installed.** If the user doesn't have it, surface that early.
- **`localhost` inside the container is not the host.** If the agent calls an MCP server running on the user's machine, the URL must be `http://host.docker.internal:<port>` not `http://localhost:<port>`. This trips up everyone the first time.
- **Folder mounts are explicit.** The agent only sees what you mount. Default to read-only unless writes are clearly required.

## Connecting agents to each other

This is the part Apollo's Artemis City work cares about most: **every running agent is already an MCP server on localhost.** No special setup required. To make agent A call agent B:

1. Start agent B and open its **Connect** dialog.
2. Copy its **MCP server (SSE)** URL.
3. Register that URL as an MCP server in the catalog (Add-ons → MCP → Add → SSE).
4. Enable that MCP server in agent A's Capabilities.

Agent A now sees agent B as a single tool. B's internal tools and prompt are *not* exposed — only the conversational interface. That's the whole orchestration story; it composes recursively.

For the full pattern (coordinator + specialists, plus how this maps to ATP agent profiles), see `references/orchestration.md`.

## Skills: the cross-compatibility win

The skill catalog accepts skills three ways:

- **Author in place** — drop a folder with `SKILL.md` into `skills/` in the agent project.
- **Add from GitHub** — Add-ons → Skills → Add → owner/repo (+ optional skill name). The repo just needs a folder containing `SKILL.md`.
- **Inherit from a plugin** — plugins ship skills that auto-register.

The frontmatter format Agent Studio reads is the same `name` + `description` Claude uses. The body is interpreted the same way. So when authoring:

- Write the skill once.
- Put it in a GitHub repo (or local folder).
- It works in both ecosystems.

When migrating an existing Claude skill into Agent Studio, the migration is almost always *zero edits* — but read `references/skills_in_anaconda.md` for the small differences in how Anaconda discovers and triggers them, and for the security scanner that runs over imported skills.

## Tool servers: shared tools without a model

A tool server is "an agent with no model" — pure MCP server exposing Python tools, no system prompt, no conversation. Reach for this when:

- Multiple agents need the same set of Python tools and you don't want to duplicate them.
- You want to expose a tool collection to external clients (Claude Desktop, Cursor, VS Code) without bundling an LLM.

Build it the same way as an agent's `tools/` directory; start it; copy the SSE URL; register elsewhere. That's the whole loop.

## AI provider note

Agent Studio ships with two built-in providers you can't delete: **Anaconda** (hosted; Claude Sonnet 4.6 is the default, plus Haiku 4.5, GPT-OSS 120B, and the Nova family) and **Anaconda Desktop** (whatever local model server is running on the machine). Add OpenAI / Anthropic / Google / Groq with an API key, or define a Custom Provider against any compatible endpoint. Models surface automatically once the provider is connected.

When picking a provider in `agent.yaml`, the Anaconda Desktop provider is the right default for local-only / offline / privacy-sensitive workflows. The Anaconda hosted provider is the right default when the user just wants it to work.

## Workflow patterns (when the user asks for an agent)

These cover ~90% of incoming requests. Pick the one that matches and execute:

### Pattern A — "Build me an agent that does X"

Read `references/build_and_run.md` for the full command walkthrough; the shape is:

1. Ask one clarifying question max: hosted or local model? (Defaults: hosted if unspecified.)
2. Scaffold the directory structure (copy `assets/` templates).
3. Fill `agent.yaml` with: name, provider, model, system prompt, capability list.
4. Author the Python tools the agent will need in `tools/<module>.py`.
5. If the work is procedural rather than primitive, also write a `skills/<skill-name>/SKILL.md`.
6. **Resolve the environment**: `pixi install`, then `pixi run python -c "import anaconda_agent_runtime"` to confirm the runtime is in place. A failed solve is easier to read here than inside the app.
7. **Preflight-validate**: `python scripts/validate_agent.py <project> --strict` and fix every error. This catches the config mistakes Agent Studio reports as a single opaque failure.
8. Tell the user how to load the project: open Agent Studio → Agents → drag the folder, or use the **Open** menu pattern to point Agent Studio at it.
9. **Verify it loaded**: confirm every `@tool` appears, the provider/model resolves, and listed skills show up — then smoke-test with one prompt that forces a real tool call. If a check fails, go to `references/troubleshooting.md`.

### Pattern B — "Register this MCP server"

1. Read `references/orchestration.md` (the MCP registration section).
2. Determine transport: if the server runs as a process, stdio; if it's already a URL, SSE.
3. Build either the `mcp.json` entry (in `tools/mcp.json`) or hand back exact Add-ons → MCP → Add field values.
4. If you wrote a `tools/mcp.json`, run `scripts/validate_agent.py` — it verifies each server's transport fields and catches the classic `localhost`-from-sandbox mistake (use `host.docker.internal`).

### Pattern C — "Migrate this Claude skill into Anaconda"

1. Confirm the existing skill has valid frontmatter (`name`, `description`).
2. Drop it in `skills/<skill-name>/SKILL.md` in the agent project, OR publish it to GitHub and tell the user to add it via owner/repo.
3. Recommend they run the security scan (Add-ons → Skills → select → Security → Start scan) the first time, especially if Deep scan with AI is available.

### Pattern D — "Make agent X call agent Y" (orchestration)

1. Read `references/orchestration.md`.
2. Confirm both agents run cleanly first.
3. Walk the user through the Connect → copy SSE URL → register as MCP → enable on caller loop.
4. If A can't reach B (connection refused, no tools), check `references/troubleshooting.md` → section F: B not running, wrong port, or `localhost` used from inside A's sandbox.

## Anti-patterns to head off

- **Don't recreate Claude-skill content from scratch when migrating.** The format is identical; copy the file.
- **Don't put secrets in `agent.yaml` or `mcp.json`.** Use the agent's environment variable config or the AI provider key flow. Files in the project folder may end up in version control or shared archives.
- **Don't confuse `tools/mcp.json` with the global Add-ons → MCP catalog.** `mcp.json` is project-scoped; the catalog is desktop-wide. Use the catalog for anything shared across agents; use `tools/mcp.json` for project-specific server config.
- **Don't write a tool when a skill is the right answer.** If the "thing the agent needs" is a procedure rather than a new capability, write a SKILL.md instead — same primitives, less code, easier to revise.

## Apollo-specific notes

(Loaded because this skill is authored inside the Artemis City project.)

- Agent Studio's "every agent is an MCP server on localhost" model is the cleanest possible substrate for the Artemis-City multi-agent architecture (`Artemis-Oracle`, `Compsuite`, `Packrat`, `Compressor`, `Codex`). Each ATP persona maps cleanly to one Agent Studio agent.
- ATP headers live naturally as a **Skill** (workflow), not a Python tool. The `artemis-transmission-protocol` skill already in this project can be dropped into `skills/atp/SKILL.md` of any Agent Studio agent unchanged.
- The Validators Toolkit and `atp_validator.py` are good candidates for a **Tool Server** — they're pure functions, no model, useful across multiple agents.
- The Oracle Watcher v0.2 work (capability tickets, CNKD, sentinels) lives a layer below Agent Studio. Agent Studio's sandbox + Docker isolation covers Watcher's L0 "containment" tier out of the box; the higher tiers (L1–L6) would sit alongside, not inside, Agent Studio.
- For the Hall Monitor methodology, Agent Studio's **Agent Monitor** panel (Timeline / By Agent / Reset) is a ready-made observation surface. Worth noting as a complement to the planned Power BI layer.

## Source

Anaconda Agent Studio documentation, originally fetched May 2026:
- https://www.anaconda.com/docs/tools/anaconda-desktop/agent-studio/main
- /agents, /skills, /mcp-servers, /tool-servers, /ai-providers

Build/run, troubleshooting, and the preflight validator were added June 2026, grounded against:
- https://www.anaconda.com/docs/reference/troubleshooting (Desktop + conda/pixi error catalog)
- the pixi command surface (`init` / `add` / `install` / `run`) and the documented agent.yaml / pixi.toml / mcp.json schemas in this skill's references
- the full docs index at https://www.anaconda.com/docs/llms.txt

`references/troubleshooting.md` marks each entry **[docs]** vs **[operational]** so you know what's doc-sourced and what's reasoned platform behavior. When this skill's facts drift from current Anaconda docs, re-fetch (start from `llms.txt`) and update. The product is in Beta and changes.
