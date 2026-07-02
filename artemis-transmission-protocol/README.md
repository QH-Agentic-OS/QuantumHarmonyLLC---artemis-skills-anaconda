# artemis-transmission-protocol

Structured communication using the Artemis Transmission Protocol (ATP). Wraps every agent response in a normalized header so multi-agent systems share a common envelope.

## What it does

When an agent has this skill enabled, it:

1. Always emits an ATP header before responding (10 standardized fields).
2. Applies persona-driven response framing based on the header's `Action Type` (REFLECTIVE / ARCHITECTURAL / TECHNICAL / CONVERSATIONAL / POETIC).
3. Tracks ATP tag evolution in a SQLite registry so the vocabulary can grow without losing history.

The header looks like:

```
[[Agent_Profile]]: Artemis-Oracle
[[Mode]]: Synthesize
[[Context]]: Navigate the knowledge graph
[[Priority]]: Normal
[[Action Type]]: Reflect
[[TargetZone]]: /home/apollo/artemis-city
[[Special Instructions]]: None
[[Output_Type]]: inline chat
[[Context_Source]]: TBD
[[Free_Text_Prompt]]: ATP Mission Control
```

## Installation in Anaconda Agent Studio

**From this repo (recommended):**

1. Add-ons → Skills → Add
2. Owner: `<your-github-username>`
3. Repository: `artemis-skills-anaconda`
4. Skill name: `artemis-transmission-protocol`
5. Add to Catalog → run Security scan → enable on your agent

**Bundled into an agent project:**

Copy this folder to `<your-agent-project>/skills/atp/`. The skill loads on agent startup. See the `artemis-oracle` reference project for an example.

## What's in this skill

```
artemis-transmission-protocol/
├── SKILL.md               # the entry point — describes ATP and the response rules
└── references/
    ├── atp_schema.sql     # SQLite schema for the tag registry
    ├── persona.py         # ArtemisPersona class with mode-based framing
    ├── reflection.py      # Reflection engine + concept graph
    └── semantic_tagging.py # Tag extraction + citation tracking
```

The SKILL.md body is loaded into the agent's context when the skill triggers. The `references/` files are loaded on demand — only when the skill explicitly points the agent at them.

## Trigger phrases

This skill activates when the user (or another agent) says things like:

- "Format this as ATP"
- "Add the ATP header"
- "Use the Artemis Transmission Protocol"
- "Send this through ATP to <other agent>"
- Anything where the active agent is `Artemis-Oracle`, `Compsuite`, `Packrat`, `Compressor`, or `Codex`.

It also auto-triggers for agent-to-agent MCP calls in Anaconda Agent Studio when the upstream agent has this skill enabled and is calling another agent over its SSE endpoint.

## Persona mode mapping

| ATP `Action Type` | Persona ResponseMode | Effect |
|---|---|---|
| `Summarize` | REFLECTIVE | "Let me reflect on this..." framing |
| `Scaffold` | ARCHITECTURAL | "From an architectural perspective..." framing |
| `Execute` | TECHNICAL | Direct, code-focused |
| `Reflect` | REFLECTIVE | Deep analysis, connection-drawing |

See `references/persona.py` for the full phrase banks and the `set_mode()` / `format_response()` API.

## Tag registry

The skill maintains a SQLite tag registry to track ATP tags and their definitions over time. To initialize:

```bash
sqlite3 atp_registry.db < references/atp_schema.sql
```

Mount the database into the agent's sandbox via `agent.yaml`:

```yaml
sandbox:
  mounts:
    - host_path: ~/atp-registry
      sandbox_path: /work/registry
      mode: rw
```

The agent can then read and write `/work/registry/atp_registry.db` from its tools.

## Notes

- **Cross-compatibility:** This SKILL.md works unchanged in Claude. The `references/` Python files are reachable from both environments — the skill body never assumes a specific runtime.
- **Token discipline:** The ATP header is meant to be lightweight. If the agent is generating ATP headers that exceed ~120 tokens, something has gone wrong upstream (likely the `Context` field is too verbose).
- **Inter-agent use:** When agent A calls agent B over MCP, A should wrap its outgoing prompt with an ATP header so B's response is correctly scoped. B's own ATP skill then validates the incoming header and responds in kind.
