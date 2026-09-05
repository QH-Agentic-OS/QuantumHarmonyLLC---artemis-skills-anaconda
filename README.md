# Artemis Skills for Anaconda Agent Studio

Agent skills from the Artemis City project, packaged for [Anaconda Agent Studio](https://www.anaconda.com/docs/tools/anaconda-desktop/agent-studio/main).

This repo holds skills authored for [Anaconda Agent Studio](https://www.anaconda.com/docs/tools/anaconda-desktop/agent-studio/main). Each skill is also format-compatible with Claude (same SKILL.md frontmatter), so any skill in this repo can be used in both ecosystems. The repo doubles as a [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces), so the whole skill set can be integrated with two commands.

## Skills

| Skill | What it does |
|---|---|
| [`anaconda-agent-studio`](./plugins/anaconda-agent-studio/skills/anaconda-agent-studio) | Scaffolds and configures agents for Anaconda Agent Studio — `agent.yaml`/`pixi.toml` layout, `@tool` authoring on `anaconda_agent_runtime`, MCP tool servers, multi-agent orchestration, and migrating existing Claude skills into the Agent Studio catalog. |
| [`artemis-transmission-protocol`](./plugins/artemis-transmission-protocol/skills/artemis-transmission-protocol) | Wraps agent communication in a normalized ATP header so multi-agent systems share a common envelope. Includes the `ArtemisPersona` class for mode-aware response framing, plus reflection and semantic-tagging helpers and a pre-seeded SQLite tag registry. |

More to come as Artemis City components migrate over (validators, reflection, semantic tagging as standalone skills).

## Repository layout

The repo is organized as a plugin marketplace; each skill lives inside its plugin under `skills/`:

```
QuantumHarmonyLLC---artemis-skills-anaconda/
├── .claude-plugin/
│   └── marketplace.json              # marketplace manifest (owner, plugins)
└── plugins/
    ├── anaconda-agent-studio/
    │   ├── .claude-plugin/
    │   │   └── plugin.json
    │   └── skills/
    │       └── anaconda-agent-studio/
    │           ├── SKILL.md          # required: frontmatter (name, description) + body
    │           ├── references/       # loaded on demand (specs, guides)
    │           ├── scripts/          # validate_agent.py
    │           └── assets/           # agent.yaml / pixi.toml / SKILL.md templates
    └── artemis-transmission-protocol/
        ├── .claude-plugin/
        │   └── plugin.json
        └── skills/
            └── artemis-transmission-protocol/
                ├── SKILL.md          # required: frontmatter (name, description) + body
                ├── scripts/          # persona.py, reflection.py, semantic_tagging.py
                \/assets/          # optional: templates, fonts, images
```

The `SKILL.md` frontmatter requires `name` and `description`. The `name` is the stable invocation name (unchanged by folder moves); the `description` is the primary trigger — the agent reads it to decide whether to consult the skill.

## Installing a skill in Anaconda Agent Studio

Agent Studio imports skills directly from a public GitHub repo by scanning it for `SKILL.md` files.

1. Open Anaconda Desktop → enable **Agent Studio** under Beta features.
2. Launch Agent Studio → **Add-ons** → **Skills** → **Add**.
3. Enter:
   - **Owner**: `AgenticGovernace` (or your GitHub username)
   - **Repository**: `QuantumHarmonyLLC---artemis-skills-anaconda` (or `artemis-skills-anaconda`)
   - **Skill name**: `anaconda-agent-studio` or `artemis-transmission-protocol` (or leave blank to import every skill in the repo)
4. **Add to Catalog.**
5. (Recommended) Select the skill in the catalog → **Security** → **Start scan**. Enable **Deep scan with AI** if a provider is configured.
6. To enable the skill on an agent: open the agent's config page → **Add Capability** → **Skill** → check the box → **Save**.

## Installing a skill in Claude manually

The same `SKILL.md` works in Claude without modification. You can add the repo as a marketplace (recommended) or install a skill manually.

```bash
# Add the repo as a Claude plugin marketplace
/plugin marketplace add https://github.com/AgenticGovernace/QuantumHarmonyLLC---artemis-skills-anaconda.git

# Or copy a single skill folder into Claude's skills directory:
# cp -r plugins/<plugin-name>/skills/<skill-name>/ ~/.claude/skills/<skill-name>/
```

## Skill structure

Skills live under `skills/`, the directory Claude Code plugins auto-discover. Each skill folder follows the standard layout:

```
skills/<skill-name>/
├── SKILL.md         # required: frontmatter (name, description) + body
├── references/      # loaded on demand
│   ├── *.md         # additional Markdown context
│   └── *.py         # Python modules the skill points the agent at
├── scripts/         # optional: executable helpers
└── assets/          # optional: templates, fonts, images
```
```

## Authoring a new skill

1. To author as a plugin: create a folder under `plugins/<plugin-name>/skills/<skill-name>/` and add a `SKILL.md` with valid frontmatter (`name`, `description`). Put reference material in `references/` and executable helpers in `scripts/`; point the body at them. Register the plugin in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) and commit/push.

2. To author directly for Claude: create a folder under `skills/` with `SKILL.md` and the supporting `references/`, `scripts/`, and `assets/` as needed. Commit and push; Claude Code picks it up on the next marketplace update.

See [`plugins/artemis-transmission-protocol/skills/artemis-transmission-protocol/SKILL.md`](./plugins/artemis-transmission-protocol/skills/artemis-transmission-protocol/SKILL.md) as a worked example.

## License

Apache-2.0. See [LICENSE](./LICENSE).
