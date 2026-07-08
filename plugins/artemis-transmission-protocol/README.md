# Artemis Transmission Protocol (ATP)

An agent skill that packages the **Artemis Transmission Protocol** — a standardized
header and scoped response system for normalizing context and coordinating agent-to-agent
communication. Packaged for **Anaconda Agent Studio** and format-compatible with Claude
(same `SKILL.md`, importable in both).

## What it provides

- **ATP header** — a fixed-order tag block (`Agent_Profile`, `Mode`, `Context`, `Priority`,
  `Action Type`, `TargetZone`, `Special Instructions`, `Output_Type`, `Context_Source`,
  `Free_Text_Prompt`) emitted before each response.
- **Action Type → ResponseMode mapping** — drives the shape of the reply (Summarize, Scaffold,
  Execute, Reflect).
- **Artemis persona layer** (`skills/.../scripts/persona.py`) — reflective / architectural /
  technical / conversational / poetic framing modes.
- **Reflection + semantic tagging** (`reflection.py`, `semantic_tagging.py`) — concept
  extraction, clustering, narrative synthesis, and tag/citation handling.
- **Pre-seeded tag registry** (`assets/atp_registry.db`, schema in `assets/atp_schema.sql`) —
  ~29 tags tracking the header fields and their known values.

## Layout

```
artemis-transmission-protocol/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── artemis-transmission-protocol/
        ├── SKILL.md
        ├── scripts/   (persona.py, reflection.py, semantic_tagging.py)
        └── assets/    (atp_registry.db, atp_schema.sql)
```

The skill's invocation name comes from the `name` field in `SKILL.md` frontmatter, so it stays
stable across updates. Once installed, invoke it by mentioning ATP / the Artemis
protocol, or by asking for a multi-step or agent-to-agent task.

## Install

### Anaconda Agent Studio
Agent Studio → **Add-ons** → **Skills** → **Add**, then enter owner `AgenticGovernace`,
repository `QuantumHarmonyLLC---artemis-skills-anaconda`, skill name
`artemis-transmission-protocol`. See the [repo README](../../README.md) for the full walkthrough
(catalog, security scan, enabling on an agent).

### Claude
Copy the `skills/artemis-transmission-protocol/` folder into `~/.claude/skills/`, or add the repo
as a plugin marketplace:

```
/plugin marketplace add https://github.com/AgenticGovernace/QuantumHarmonyLLC---artemis-skills-anaconda.git
```

## License

Apache-2.0. See `LICENSE`.
