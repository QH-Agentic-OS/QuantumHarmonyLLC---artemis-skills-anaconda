# Multi-agent orchestration

The thing that makes Agent Studio interesting beyond "another local agent runner" is this: **every running agent automatically exposes itself as an MCP server on localhost.** No extra config, no separate process, no plumbing to write. If agent A is running, agent B can call it as a tool.

This page is the how, the gotchas, and the patterns.

## The basic wiring

To make agent A call agent B:

1. **Start agent B.** From its config page, hit **Start**. Wait for the "ready" notification.
2. **Open agent B's Connect dialog.** Same config page → **Connect** button (top-right area).
3. **Copy the MCP server (SSE) URL.** It'll look like `http://localhost:NNNN/sse`.
4. **Register that URL in the global MCP catalog.** Add-ons → MCP → Add → SSE → paste URL → give it a name like `agent-b`.
5. **Enable on agent A.** On agent A's config page: Capabilities → Add Capability → MCP Server → check `agent-b` → Save.

Agent A now has one new tool, named for the agent (something like `agent_b_chat`). Calling it sends a prompt to agent B; agent B replies; agent A treats the reply as the tool's return value.

That's the entire orchestration mechanism. Everything else is variations on this loop.

## What gets exposed, what doesn't

When agent A calls agent B, what crosses the boundary:

- Agent A sends: a text prompt.
- Agent B receives: the prompt, processed by *its own* system prompt, tools, and skills.
- Agent A receives back: agent B's response text. That's it.

What does NOT cross:

- Agent B's internal tool calls. A doesn't see what tools B used.
- Agent B's system prompt or skills. A only sees the conversational surface.
- Agent B's documents, conversation history, or model choice. Opaque.

This isolation is the feature. It means you can swap implementations of B without changing A. It also means: **if you need agent A to know which specific tools B used, you have to put that in B's response text explicitly.** Mention it in B's system prompt.

## Patterns that work

### Coordinator + specialists

The simplest useful pattern. One coordinator agent does no real work; it just routes user requests to specialists.

```
        ┌─── code-reviewer (specialist)
user → coordinator ─┼─── doc-lookup (specialist)
        └─── test-runner (specialist)
```

The coordinator's system prompt is mostly: "If the user asks about X, ask the code-reviewer agent. If about Y, ask doc-lookup..." Each specialist has deep tools/skills in its narrow domain.

When this is the right shape:
- You have ≥3 distinct expertise areas and want clean separation.
- Different specialists need different model choices (e.g., reviewer on Sonnet, doc-lookup on Haiku for cost).
- Specialists may evolve independently.

When it's the wrong shape:
- Everything is one domain with a few sub-skills. A single agent with multiple skills is simpler.
- The "routing" decision is trivial — then the coordinator is just overhead.

### Pipeline (linear hand-off)

Agent A → Agent B → Agent C. Each does one transformation step.

```
raw-input → cleaner → analyzer → summarizer → output
```

Usually NOT the right shape in Agent Studio, because Agent Studio agents are conversational, not stream-processors. If your problem is genuinely "step 1, then step 2, then step 3 with no branching," that's a *pipeline*, and a pipeline wants code (a Python script with three function calls) more than it wants agents.

When this *is* right: when each step legitimately needs LLM-level judgment and the steps are loose enough that branching might happen later.

### Hub-and-spoke (mesh of specialists)

Several specialists, no fixed coordinator, each can call the others. This is where Apollo's Artemis City work lives: Artemis-Oracle, Compsuite, Packrat, Compressor, Codex all collaborating.

Caveats from experience:
- Without a coordinator, the user has to know which agent to talk to. Build a coordinator unless this is acceptable.
- Cycles are possible. Agent Studio doesn't (as of May 2026) detect them. Be deliberate about who calls whom.
- Cost compounds quickly. Five agents, each one round-trip per turn, can rack up tokens fast.

## Connecting from outside Agent Studio

The same SSE URL that agents inside Agent Studio use is reachable from anything that speaks MCP:

- **Claude Desktop** — add the URL as an MCP server in Claude Desktop's settings.
- **Cursor** — paste the `mcp.json` snippet from the Connect dialog into Cursor's MCP settings (the dialog provides a paste-ready config).
- **VS Code** — same idea via the VS Code MCP client extension.
- **Custom MCP client** — any MCP SDK can connect to the URL.

This means an Agent Studio agent can be the backend for a Claude Desktop conversation, or the team of a Cursor IDE session, or a piece in any other workflow. It's not Agent-Studio-internal infrastructure; it's standard MCP.

## Tool servers as orchestration components

A **tool server** (separate concept) is "an agent without a model." Same project structure, same `tools/` directory, but no LLM. It exposes pure Python tools over MCP.

Use a tool server when:
- Multiple agents need the same toolset and there's no good reason to load a model for it.
- You want to expose a tool collection to external clients without the bundling of agent identity.
- The Validators Toolkit / `atp_validator.py` is a perfect example — pure functions, useful from anywhere.

Tool servers participate in the orchestration pattern exactly like agents: start it, copy its SSE URL, register, enable. The only difference is consumers see Python tools directly, not a conversational interface.

## The sandbox networking gotcha (still)

Worth restating because this is *the* bug:

If agent A is running with sandbox enabled (the default) and you give it agent B's URL as `http://localhost:NNNN/sse`, A can't reach B. Inside A's container, `localhost` is the container's own loopback, not the host.

Fix: register the URL as `http://host.docker.internal:NNNN/sse`. Agent Studio's UI sometimes does this for you when adding from inside the app; verify by checking the registered URL in Add-ons → MCP.

If both agents A and B are running with sandbox enabled, this routing still works because Agent Studio publishes each agent's port to the host network (when `network: outbound` is set, which is the default). `host.docker.internal` reaches the host, the host has B's port published, and the call succeeds.

If B is running with `network: isolated`, B is unreachable from A. That's by design — isolation means isolation.

## The Agent Monitor — your debugging surface

When something doesn't work, the Agent Monitor is the first place to look:

- From the Agents page → **Monitor** (top-right) → opens a dedicated window with events from all running agents.
- From inside a chat → **Monitor** button → opens a side panel scoped to that conversation.

What you see: tool calls (which agent → which tool → what arguments → what response), model requests, lifecycle events. Timeline view for chronological cross-agent debugging; By Agent view for one-at-a-time inspection.

For Apollo's Hall Monitor methodology, this is the closest thing Agent Studio gives out of the box. Pair it with the planned Power BI layer for longer-horizon analysis.

## ATP and orchestration (specific to this project)

Mapping Artemis personas to Agent Studio agents:

| ATP Persona | Agent Studio agent | Capabilities |
|---|---|---|
| Artemis-Oracle | `artemis-oracle` | ATP skill, reflection skill, broad model (Sonnet) |
| Compsuite | `compsuite` | Validators tool server (MCP), heavy compute model |
| Packrat | `packrat` | File I/O tools, Notion/Drive MCP, archival skills |
| Compressor | `compressor` | Summarization skills, smaller model (Haiku) |
| Codex | `codex` | Python tools, git MCP, code-review skill |

The ATP header itself stays as a **skill** on each agent (the `artemis-transmission-protocol` skill drops into each agent's `skills/atp/` folder). The coordination layer is the mesh of MCP connections between agents.

The Oracle Watcher v0.2 work (capability tickets, CNKD, sentinels) is a *layer beneath* this — it would govern the actual MCP transport. Agent Studio doesn't enforce Watcher tiers natively, but you can run a Watcher-aware MCP proxy in front of each agent's SSE endpoint to add those guarantees without changing the agent itself.
