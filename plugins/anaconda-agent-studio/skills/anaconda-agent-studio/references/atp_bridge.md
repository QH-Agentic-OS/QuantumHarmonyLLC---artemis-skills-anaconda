# ATP ↔ Agent Studio bridge

This reference is specific to the Artemis City project. Load it when the user wants ATP, Validators Toolkit, Hall Monitor, or any Artemis-City concept to run inside Anaconda Agent Studio.

## The mapping in one table

| Artemis City concept | Agent Studio mechanism |
|---|---|
| ATP persona (Artemis-Oracle, etc.) | One agent per persona, distinct `agent.yaml` |
| ATP header format | A bundled skill (`skills/atp/SKILL.md`) on each agent |
| Validators Toolkit | A **tool server** (no model, just `@tool` functions) |
| `atp_validator.py` | A Python tool inside the validators tool server |
| MCP Watcher v0.1 / v0.2 | An MCP proxy sitting *in front of* Agent Studio's SSE endpoints |
| Hall Monitor | Agent Studio's **Agent Monitor** panel + Power BI export |
| Hebbian weights / agent registry | Coordinator agent's system prompt + capability set |
| Obsidian vault write-out | A Python tool that writes to a mounted vault folder |
| ATP Mission Control dashboard | Stays external — calls Agent Studio's HTTP endpoint per agent |

## Why this mapping holds

Agent Studio's design accidentally mirrors Artemis City's design more than coincidence allows for: both treat agents as first-class entities with isolation boundaries, both use MCP as the inter-agent transport, both separate procedural knowledge (skills) from primitive capability (tools). The Artemis City work and the Agent Studio product appear to be converging on the same shape from different starting points.

The practical consequence: porting Artemis City onto Agent Studio is mostly *naming and packaging*, not redesign.

## Suggested project layout for the Artemis City port

```
artemis-city-anaconda/
├── agents/
│   ├── artemis-oracle/
│   │   ├── agent.yaml
│   │   ├── pixi.toml
│   │   ├── skills/
│   │   │   ├── atp/SKILL.md            # the existing ATP skill, unchanged
│   │   │   └── reflection/SKILL.md
│   │   ├── tools/
│   │   │   └── mcp.json                # points at validators-tool-server
│   │   └── documents/
│   │       └── personality.md           # short, dense persona doc
│   ├── compsuite/
│   ├── packrat/
│   ├── compressor/
│   └── codex/
└── tool-servers/
    └── validators/
        ├── agent.yaml                   # tool server, no model
        ├── pixi.toml
        └── tools/
            ├── __init__.py
            ├── atp_validator.py         # ports the existing module
            ├── encoding_check.py
            └── cross_field.py
```

Each agent folder is an Agent Studio project the user can open with **Agents → Open**. The tool server folder is opened with **Tool Servers → Open**. Agent Studio shows them all in one workspace.

## The ATP skill — drop-in version

The existing `/mnt/skills/user/artemis-transmission-protocol/` directory is already Agent-Studio-compatible. To use it:

1. Copy the folder to `<agent-project>/skills/atp/`.
2. In the skill's frontmatter, append Agent Studio trigger phrases to the `description`. Specifically: "Use this when running inside Agent Studio and the agent needs to emit an ATP header before responding to inter-agent MCP calls."
3. Enable the skill on each agent's Capabilities row.

The skill body works unchanged. The persona phrase banks and the Action Type → ResponseMode mapping apply identically.

## The Validators Toolkit as a tool server

The v0.1 toolkit currently lives inside the ATP Mission Control React dashboard (`atp-mission-control.jsx`). To make it reusable across the agent mesh:

1. Port the validation rules from JavaScript to Python in `tool-servers/validators/tools/atp_validator.py`.
2. Wrap each check (`validate_agent`, `validate_mode`, ...) and the cross-field validators (`mode_action_coherence`, `critical_context_check`, `execute_target_check`, `encoding_check`) as `@tool` functions.
3. Optionally expose a top-level `validate_atp_header(header_yaml: str) -> dict` tool that runs all checks and returns the score data.

Now every Artemis agent can call `validate_atp_header(...)` before transmitting. The Hall Monitor pattern emerges naturally: a separate `hall-monitor` agent calls the validator on outgoing messages from other agents and logs results — without those agents knowing they're being audited (the observer-effect concern).

## Hall Monitor inside Agent Studio

The Hall Monitor methodology says: Claude validates AI-generated code against documentation baselines, isolated from the tested model's context.

In Agent Studio, that decomposes into:

- A `hall-monitor` agent (Claude-backed) with no MCP connection to the agents it watches.
- A `validators` tool server it uses to check outputs.
- An Obsidian / Notion write-out tool for findings.
- The Agent Monitor view (real-time) for human spot-checks.
- An export from Agent Monitor's event stream → Power BI for longer-horizon pattern analysis. The docs don't (May 2026) publish a documented export format for the monitor stream; this likely needs a Python tool that subscribes to a project's event log directly. Investigate when the time comes.

The key isolation property — tested agent doesn't know it's being watched — holds because in Agent Studio's model, an agent only sees the MCP servers it's wired to. The hall-monitor doesn't appear in the tested agent's capability list, so the tested agent has no signal of being observed.

## Oracle Watcher v0.2 alongside Agent Studio

Watcher v0.2 (tiered trust, CNKD, sentinels) is a layer *beneath* MCP transport. Agent Studio handles:

- **L0 (containment)** — Docker sandbox with the same `CapDrop: ALL` / no-net / resource-limit behavior the Watcher specifies. ✅ ships with Agent Studio.

Agent Studio does NOT handle:

- **L1 (mTLS)** — SSE endpoints are HTTP, not mTLS.
- **L2 (CNKD signing)** — no chained-nonce key derivation in MCP transport.
- **L3 (manifest provenance)** — MCP servers don't sign their manifests.
- **L4 (token scope)** — Agent Studio uses approval prompts, not scoped tokens.
- **L5 (build attestation)** — agents are folders on disk; no cosign verify.
- **L6 (sentinels)** — Agent Monitor is observation, not active sentinel network.

To get Watcher v0.2 properties on top of Agent Studio, run a Watcher-aware MCP proxy between agents: agent A's outbound MCP calls go through the proxy, which enforces L1–L6, then forwards to agent B. Each agent's `tools/mcp.json` registers the proxy's URL rather than B's direct URL. This adds the security tiers without touching Agent Studio internals.

## What stays external

A few Artemis City components have no good Agent-Studio-native home and should stay external:

- **ATP Mission Control dashboard** (React). It's a *human* UI for building ATP headers. It calls Agent Studio's HTTP API to dispatch headers to the right agent. Don't try to port it into a skill or a tool.
- **The Notion methodology hub.** Notion stays Notion. An agent can write findings to Notion via the Notion MCP, but the human-authored methodology pages live in Notion.
- **The `mcp-watcher-extension-v0.2.md` spec itself.** It's a design doc, not an artifact Agent Studio consumes. Keep it in the repo / Notion.

## What this skill explicitly does NOT do

This skill doesn't write Python code to *implement* the validator or the Watcher proxy — those are real engineering projects with their own lifecycle. The skill helps you scaffold the *Agent Studio housing* for that work. The Python implementations are next-step work for the user.

When the user asks to actually build the validator or the proxy, hand them to the `mcp-builder` skill (for MCP-server work) or just write the Python directly (for the validator).
