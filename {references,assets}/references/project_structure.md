# Project structure — the full walkthrough

When the user wants to build or hand-edit an Agent Studio agent, this is the layout. Every file has a purpose; don't add unnecessary ones.

```
my-agent/
├── agent.yaml
├── pixi.toml
├── documents/
├── packages/
│   └── anaconda_agent_runtime-X.Y.Z-py3-none-any.whl
├── skills/
│   └── <skill-name>/
│       └── SKILL.md
├── tools/
│   ├── __init__.py
│   ├── <module>.py
│   └── mcp.json
└── tree.md          # optional, human-friendly map
```

## `agent.yaml`

The root manifest. Agent Studio reads this to render the agent's configuration page and to launch the runtime. See `references/agent_yaml_spec.md` for the field-by-field spec. At minimum it carries:

- agent name, description
- AI provider + model (must match a provider configured in Agent Studio)
- system prompt
- references to skills, tool modules, MCP servers
- sandbox settings (network mode, CPU/memory caps, folder mounts)

This file is the one the user will most often hand-edit. Keep it human-readable and commented.

## `pixi.toml`

Pixi is Anaconda's package manager (the spiritual successor to conda environments for projects). `pixi.toml` declares dependencies and tasks. For an Agent Studio agent the critical line is the dependency on `anaconda_agent_runtime` (usually pulled from `packages/` for offline use). When the user adds Python packages to their tools through the Agent Studio UI, those land here.

Don't hand-edit unless the user asks — Agent Studio manages it through the **Dependencies** dialog on the tools editor. But know what it is so you don't break it.

## `documents/`

Reference files that get inserted into the agent's context window at the start of every conversation. Think: domain glossary, style guide, a small dataset of facts the agent always needs at hand.

Constraints:
- 25 MB max per file.
- Whatever goes here eats from the context budget on every turn — keep these tight, summary-style, not raw transcripts or full books.

When to use it: facts the agent ALWAYS needs. When NOT to use it: large reference material the agent only sometimes consults — that should live behind a tool (e.g., a `search_docs` Python tool that reads from a local vector store).

## `packages/`

Local Python wheels bundled into the project. The Agent Studio runtime (`anaconda_agent_runtime-*.whl`) lives here. The pattern lets agents run fully offline once the bundle is shipped. Don't put random pip packages here unless the user has a specific reason (air-gapped deployment, version pinning a fork, etc.).

## `skills/`

Each subdirectory is one skill. The minimum is a `SKILL.md` with valid frontmatter (`name`, `description`). Bigger skills can add `scripts/`, `references/`, `assets/` exactly like the Claude skill format — Agent Studio reads them the same way.

The skills here are *bundled with this agent*. They are different from the **global skill catalog** under Add-ons → Skills (which is shared across all agents on the machine). Use bundled when the skill is specific to this agent's purpose; use the catalog when reuse across agents matters.

## `tools/`

Python tool modules + an `mcp.json` for project-local MCP server config.

- `tools/__init__.py` — usually empty; just makes Python treat the directory as a package.
- `tools/<module>.py` — one file per logical grouping of tools. Inside, every `@tool`-decorated function becomes a callable tool. See `references/tool_authoring.md`.
- `tools/mcp.json` — stdio/SSE configs for MCP servers this *specific* agent talks to. Distinct from the desktop-wide catalog.

## `tree.md`

Optional. A human-friendly outline of what's in the project. Useful when handing the project to a collaborator or pasting into Notion. Generate it from the actual directory with `tree -L 3 > tree.md` if needed; don't hand-curate.

## What goes where — quick rules

| The user wants... | Put it in... |
|---|---|
| A function the agent can call | `tools/<module>.py` as `@tool` |
| An external API or service | `tools/mcp.json` (project) or Add-ons → MCP (global) |
| Procedural guidance on combining tools | `skills/<name>/SKILL.md` |
| Facts the agent always needs | `documents/<file>` |
| Facts the agent sometimes needs | A search tool + local store |
| A reusable bundle of MCP + skills | A Plugin (Anaconda-published only as of May 2026) |

## Bootstrapping a new project

When scaffolding from scratch, write files in this order so the user can validate each step:

1. `agent.yaml` with name, description, provider, model, system prompt (nothing else yet).
2. `pixi.toml` from the template.
3. `tools/__init__.py` (empty) + one starter `tools/main.py` with a single `@tool` to prove it loads.
4. `documents/` (empty or with one short README the agent reads).
5. `skills/` only when there's a real skill to add.
6. `mcp.json` only when there's an external server to wire.

Tell the user to point Agent Studio at the folder via **Agents → Open** (or drag-drop on the Agents page). Agent Studio reads `agent.yaml` and surfaces everything in the UI.
