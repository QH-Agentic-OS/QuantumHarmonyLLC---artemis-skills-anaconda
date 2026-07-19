# QuantumHarmonyLLC---artemis-skills-anaconda

Anaconda Agent Studio skills from the Artemis City project.

This repo holds skills authored for [Anaconda Agent Studio](https://www.anaconda.com/docs/tools/anaconda-desktop/agent-studio/main). Each skill is also format-compatible with Claude (same SKILL.md frontmatter), so any skill in this repo can be used in both ecosystems. The repo doubles as a [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces), so the whole skill set can be integrated with two commands.

## Skills

| Skill | What it does |
|---|---|
| [`anaconda-agent-studio`](./skills/anaconda-agent-studio) | Scaffold, configure, and ship agents for Anaconda Agent Studio — `agent.yaml`, `pixi.toml`, `@tool` modules, `mcp.json`, skills, and multi-agent orchestration over MCP. |

More to come as Artemis City components migrate over (validators, reflection, semantic tagging as standalone skills).

## Installing via the Claude Code plugin marketplace

This repo is a Claude Code plugin marketplace (`.claude-plugin/marketplace.json`). To integrate every skill in one step:

```bash
claude plugin marketplace add AgenticGovernace/QuantumHarmonyLLC---artemis-skills-anaconda
claude plugin install artemis-anaconda-skills@artemis-skills-anaconda
```

Or interactively: run `/plugin` inside Claude Code, add the marketplace by its GitHub `owner/repo`, then install the `artemis-anaconda-skills` plugin. Skills update whenever the marketplace is refreshed (`claude plugin marketplace update artemis-skills-anaconda`).

## Installing a skill in Anaconda Agent Studio

The Agent Studio UI imports skills directly from a public GitHub repo. Once this repo is pushed to GitHub:

1. Open Anaconda Desktop → enable **Agent Studio** under Beta features.
2. Launch Agent Studio → **Add-ons** → **Skills** → **Add**.
3. Enter:
   - **Owner**: `<your-github-username>` (e.g. `apollo92`)
   - **Repository**: `artemis-skills-anaconda`
   - **Skill name**: `anaconda-agent-studio` (or leave blank to import every skill in the repo)
4. **Add to Catalog.**
5. (Recommended) Select the skill in the catalog → **Security** → **Start scan**. Enable **Deep scan with AI** if a provider is configured.
6. To enable the skill on an agent: open the agent's config page → **Add Capability** → **Skill** → check the box → **Save**.

## Installing a skill in Claude manually

The same `SKILL.md` works in Claude without modification. If you don't want the plugin marketplace route, drop a skill folder from `skills/` into wherever your Claude environment expects skills (typically `~/.claude/skills/<name>/`) or install via Claude's skill upload UI.

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

The `SKILL.md` frontmatter requires `name` and `description`. The description is the primary trigger mechanism — the agent reads it to decide whether to consult the skill.

## Authoring a new skill

1. Create a folder under `skills/`.
2. Add a `SKILL.md` with valid frontmatter.
3. Put reference material in `references/` and point the body at it.
4. Commit, push, re-import in Agent Studio (Claude Code picks it up on the next marketplace update).

See [`skills/anaconda-agent-studio/SKILL.md`](./skills/anaconda-agent-studio/SKILL.md) as a worked example.

## License

Apache-2.0. See [LICENSE](./LICENSE).
